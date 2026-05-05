from __future__ import annotations

import datetime
import logging
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Willoughby City Council"
DESCRIPTION = "Source for Willoughby City Council waste collection."
URL = "https://www.willoughby.nsw.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "18 Crabbes Avenue, North Willoughby": {
        "address": "18 Crabbes Avenue, North Willoughby, NSW 2068",
    },
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
    "Bulky Waste": "mdi:delete",
    "Street Sweeping": "mdi:broom",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address, for example: 18 Crabbes Avenue, North Willoughby, NSW 2068",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street address",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the Willoughby City Council waste service dates page, search for your address, and use the address text as shown by the lookup.",
}

BASE_URL = "https://www.willoughby.nsw.gov.au"
PAGE_URL = (
    f"{BASE_URL}/Residents/Waste-and-recycling/"
    "Household-bin-services/Waste-and-street-sweeping-services"
)

API_URLS = {
    "address_search": f"{BASE_URL}/api/v1/myarea/search",
    "collection": f"{BASE_URL}/ocapi/Public/myarea/wasteservices",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": PAGE_URL,
    "X-Requested-With": "XMLHttpRequest",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        # Establish cookies/session before the AJAX calls.
        try:
            session.get(PAGE_URL, timeout=30)
        except requests.RequestException:
            _LOGGER.debug(
                "Could not preload Willoughby page; continuing with API calls"
            )

        geolocation_id = self._get_geolocation_id(session)
        html = self._get_waste_services_html(session, geolocation_id)

        entries = self._parse_entries(html)
        entries.sort(key=lambda entry: entry.date)
        return entries

    def _get_geolocation_id(self, session: requests.Session) -> str:
        response = session.get(
            API_URLS["address_search"],
            params={"keywords": self._address},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        items = data.get("Items") or []
        if not items:
            raise SourceArgumentNotFound("address", self._address)

        if len(items) > 1:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [item.get("AddressSingleLine", "") for item in items],
            )

        geolocation_id = items[0].get("Id")
        if not geolocation_id:
            raise SourceArgumentNotFound("address", self._address)

        return geolocation_id

    def _get_waste_services_html(
        self, session: requests.Session, geolocation_id: str
    ) -> str:
        response = session.get(
            API_URLS["collection"],
            params={
                "geolocationid": geolocation_id,
                "ocsvclang": "en-AU",
            },
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("success", False):
            message = (
                data.get("message")
                or data.get("error")
                or data.get("responseMessage")
                or "Willoughby waste services API returned success=false"
            )
            raise RuntimeError(message)

        return data.get("responseContent") or ""

    @staticmethod
    def _parse_entries(html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []
        seen: set[tuple[datetime.date, str]] = set()

        service_items = soup.select("article, div.waste-services-result")

        for item in service_items:
            waste_type_el = item.find("h3")
            date_el = item.find(class_="next-service")

            if not waste_type_el or not date_el:
                continue

            waste_type = _normalise_waste_type(waste_type_el.get_text(" ", strip=True))
            date_text = date_el.get_text(" ", strip=True)
            date = _parse_date(date_text)

            if not date:
                _LOGGER.debug("Could not parse Willoughby date text: %s", date_text)
                continue

            key = (date, waste_type)
            if key in seen:
                continue

            seen.add(key)
            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                )
            )

        return entries


def _normalise_waste_type(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    lower = text.lower()

    if "recycl" in lower:
        return "Recycling"
    if "green" in lower or "garden" in lower or "organics" in lower or "fogo" in lower:
        return "Green Waste"
    if "bulky" in lower or "clean" in lower:
        return "Bulky Waste"
    if "sweep" in lower:
        return "Street Sweeping"
    if "general" in lower or "rubbish" in lower or "garbage" in lower:
        return "General Waste"

    return text


def _parse_date(text: str) -> datetime.date | None:
    text = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()

    formats = (
        "%a %d/%m/%Y",
        "%A %d/%m/%Y",
        "%d/%m/%Y",
        "%a %d %B %Y",
        "%A %d %B %Y",
        "%d %B %Y",
    )

    for date_format in formats:
        try:
            return datetime.datetime.strptime(text, date_format).date()
        except ValueError:
            pass

    slash_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", text)
    if slash_match:
        try:
            return datetime.datetime.strptime(slash_match.group(0), "%d/%m/%Y").date()
        except ValueError:
            pass

    long_match = re.search(r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b", text)
    if long_match:
        try:
            return datetime.datetime.strptime(long_match.group(0), "%d %B %Y").date()
        except ValueError:
            pass

    return None
