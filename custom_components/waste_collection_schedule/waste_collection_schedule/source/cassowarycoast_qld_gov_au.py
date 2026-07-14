from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Cassowary Coast Regional Council"
DESCRIPTION = (
    "Source for Cassowary Coast Regional Council, Far North Queensland, Australia."
)
URL = "https://www.cassowarycoast.qld.gov.au"
COUNTRY = "au"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Cassowary Coast Regional Council, "
        "for example '10 Bombala Street, Mourilyan, 4858'."
    )
}
TEST_CASES = {
    "10 Bombala Street, Mourilyan": {"address": "10 Bombala Street, Mourilyan, 4858"},
}

SEARCH_URL = "https://www.cassowarycoast.qld.gov.au/api/v1/myarea/searchfuzzy"
COLLECTION_URL = (
    "https://www.cassowarycoast.qld.gov.au/ocapi/Public/myarea/wasteservices"
)
PAGE_LINK = "/Waste-Water-and-Roads/Waste-and-Recycling/Kerbside-Collection"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": URL + PAGE_LINK,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your full street address including suburb, e.g. '10 Bombala Street, Mourilyan, 4858'",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Full Street Address",
    },
}


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")
        session.headers.update(HEADERS)

        geolocation_id = self._get_geolocation_id(session)

        response = session.get(
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

    def _get_geolocation_id(self, session) -> str:
        response = session.get(
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
