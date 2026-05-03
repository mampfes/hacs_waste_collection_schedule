from __future__ import annotations

import datetime
import logging

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Mount Alexander Shire Council"
DESCRIPTION = "Source for Mount Alexander Shire Council, VIC, Australia."
URL = "https://www.mountalexander.vic.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Campbells Creek": {"address": "123 Main Road Campbells Creek Victoria 3451"},
    "Castlemaine": {"address": "1 Mostyn Street Castlemaine Victoria 3450"},
}

ICON_MAP = {
    "general waste": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "green waste": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your full street address as it appears on the council website, e.g. '1 Mostyn Street Castlemaine Victoria 3450'.",
}

_SEARCH_URL = "https://www.mountalexander.vic.gov.au/api/v1/myarea/search"
_WASTE_URL = "https://www.mountalexander.vic.gov.au/ocapi/Public/myarea/wasteservices"
_PAGE_LINK = "/My-Property/Waste-and-recycling/Find-your-bin-collection-day"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; waste-collection-schedule)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.mountalexander.vic.gov.au" + _PAGE_LINK,
    "X-Requested-With": "XMLHttpRequest",
}


def _icon(service_name: str) -> str:
    key = service_name.lower()
    for k, v in ICON_MAP.items():
        if k in key:
            return v
    return "mdi:trash-can"


def _extrapolate(anchor: datetime.date, interval_weeks: int) -> list[datetime.date]:
    """Return all dates matching the anchor pattern within the anchor's year."""
    year = anchor.year
    delta = datetime.timedelta(weeks=interval_weeks)
    dates: list[datetime.date] = []
    d = anchor
    while d.year == year:
        dates.append(d)
        d += delta
    d = anchor - delta
    while d.year == year:
        dates.append(d)
        d -= delta
    return sorted(dates)


class Source:
    def __init__(self, address: str) -> None:
        self._address = address

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")
        session.headers.update(_HEADERS)

        r = session.get(_SEARCH_URL, params={"keywords": self._address}, timeout=30)
        r.raise_for_status()
        items = r.json().get("Items", [])
        if not items:
            raise ValueError(
                f"Address '{self._address}' not found. Check the address and try again."
            )
        geo_id = items[0]["Id"]

        r = session.get(
            _WASTE_URL,
            params={
                "geolocationid": geo_id,
                "ocsvclang": "en-AU",
                "pageLink": _PAGE_LINK,
            },
            timeout=30,
        )
        r.raise_for_status()
        html = r.json().get("responseContent", "")

        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []

        for result in soup.select(".waste-services-result"):
            name_tag = result.find("h3")
            date_tag = result.select_one(".next-service")
            if not name_tag or not date_tag:
                continue

            service_name = name_tag.get_text(strip=True)
            date_text = date_tag.get_text(strip=True)

            try:
                next_date = datetime.datetime.strptime(date_text, "%a %d/%m/%Y").date()
            except ValueError:
                _LOGGER.warning(
                    "mount_alexander_vic_gov_au: unexpected date format '%s' for '%s'",
                    date_text,
                    service_name,
                )
                continue

            note = result.select_one(".note")
            note_text = note.get_text(strip=True).lower() if note else ""
            interval = 2 if "fortnightly" in note_text else 1

            for d in _extrapolate(next_date, interval):
                entries.append(
                    Collection(date=d, t=service_name, icon=_icon(service_name))
                )

        return entries
