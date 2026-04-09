from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Ballina Shire Council"
DESCRIPTION = "Source for Ballina Shire Council, NSW, Australia."
URL = "https://www.ballina.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection-Day"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Ballina Shire Council, for example "
        "'1 Grant St, Ballina NSW 2478'."
    )
}
TEST_CASES = {
    "1 Grant St, Ballina NSW 2478": {"address": "1 Grant St, Ballina NSW 2478"}
}

SEARCH_URL = "https://www.ballina.nsw.gov.au/api/v1/myarea/searchfuzzy"
COLLECTION_URL = "https://www.ballina.nsw.gov.au/ocapi/Public/myarea/wasteservices"
PAGE_LINK = "/$8a878053-5e29-431d-896b-8c79ce08799f$/Residents/Waste-and-Recycling/Bin-Collection-Day"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": URL,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

ICON_MAP = {
    "general waste": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "green organics": "mdi:leaf",
    "food organics": "mdi:leaf",
    "garden organics": "mdi:leaf",
}


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def fetch(self) -> list[Collection]:
        geolocation_id = self._get_geolocation_id()
        response = self._session.get(
            COLLECTION_URL,
            params={
                "geolocationid": geolocation_id,
                "ocsvclang": "en-AU",
                "pageLink": PAGE_LINK,
            },
            timeout=30,
        )
        response.raise_for_status()

        html_content = response.json().get("responseContent", "")
        if not html_content:
            raise SourceArgumentNotFound("address", self._address)

        return self._parse_entries(html_content)

    def _get_geolocation_id(self) -> str:
        response = self._session.get(
            SEARCH_URL,
            params={"keywords": self._address, "maxresults": "1"},
            timeout=30,
        )
        response.raise_for_status()

        items = response.json().get("Items", [])
        if not items:
            raise SourceArgumentNotFound("address", self._address)

        geolocation_id = items[0].get("Id")
        if not geolocation_id:
            raise SourceArgumentNotFound("address", self._address)

        return geolocation_id

    def _parse_entries(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []

        for result in soup.select(".waste-services-result"):
            title = result.find("h3")
            next_service = result.select_one(".next-service")
            if title is None or next_service is None:
                continue

            waste_type = title.get_text(" ", strip=True)
            date_text = next_service.get_text(" ", strip=True)
            try:
                collection_date = datetime.strptime(date_text, "%a %d/%m/%Y").date()
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=self._guess_icon(waste_type),
                )
            )

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries

    def _guess_icon(self, waste_type: str) -> str | None:
        lower = waste_type.lower()
        for key, icon in ICON_MAP.items():
            if key in lower:
                return icon
        return None
