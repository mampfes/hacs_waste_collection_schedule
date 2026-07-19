from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Logan City Council"
DESCRIPTION = "Source for Logan City Council rubbish collection."
URL = "https://www.logan.qld.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Lee Naki's Takeaway": {"property_location": "12 Ashton Street Kingston"},
    "LCC Administration Centre": {
        "property_location": "150 Wembley Road Logan Central"
    },
    "Rochedale South (with green waste)": {
        "property_location": "53 Wendron Street Rochedale South"
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street address as used on the Logan City Council MyLogan tool "
        "(https://www.logan.qld.gov.au/MyLogan), for example "
        "'12 Ashton Street Kingston'."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "property_location": "Street Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "property_location": (
            "Your street address, e.g. '12 Ashton Street Kingston'. "
            "The closest match from the MyLogan address search is used."
        ),
    },
}

SEARCH_URL = "https://www.logan.qld.gov.au/api/v1/myarea/search"
COLLECTION_URL = "https://www.logan.qld.gov.au/ocapi/Public/myarea/wasteservices"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": URL + "/MyLogan",
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
    "green waste": Icons.ORGANIC,
}


class Source:
    def __init__(self, property_location: str):
        self._property_location = " ".join(property_location.split())
        # The property's geolocation id is a stable per-property GUID. Cache it
        # after the first lookup so subsequent (daily) fetches only need the
        # single wasteservices call instead of the address search as well.
        self._geolocation_id: str | None = None

    def fetch(self) -> list[Collection]:
        # The council site sits behind Akamai bot protection, so impersonate a
        # real browser (plain requests get a 403 Access Denied).
        session = requests.Session(impersonate="chrome")
        session.headers.update(HEADERS)

        if self._geolocation_id is not None:
            # Reuse the cached property id and skip the address search.
            try:
                return self._fetch_services(session, self._geolocation_id)
            except SourceArgumentNotFound:
                # Cached id may have gone stale; fall through to re-resolve.
                self._geolocation_id = None

        self._geolocation_id = self._get_geolocation_id(session)
        return self._fetch_services(session, self._geolocation_id)

    def _fetch_services(self, session, geolocation_id: str) -> list[Collection]:
        response = session.get(
            COLLECTION_URL,
            params={"geolocationid": geolocation_id, "ocsvclang": "en-AU"},
            timeout=30,
        )
        response.raise_for_status()

        html_content = response.json().get("responseContent", "")
        if not html_content:
            raise SourceArgumentNotFound("property_location", self._property_location)

        return self._parse_entries(html_content)

    def _get_geolocation_id(self, session) -> str:
        response = session.get(
            SEARCH_URL,
            params={"keywords": self._property_location, "maxresults": "1"},
            timeout=30,
        )
        response.raise_for_status()

        items = response.json().get("Items", [])
        if not items:
            raise SourceArgumentNotFound("property_location", self._property_location)

        geolocation_id = items[0].get("Id")
        if not geolocation_id:
            raise SourceArgumentNotFound("property_location", self._property_location)

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
                # e.g. "Monday 20 July 2026"
                collection_date = datetime.strptime(date_text, "%A %d %B %Y").date()
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
            raise SourceArgumentNotFound("property_location", self._property_location)

        return entries

    def _guess_icon(self, waste_type: str) -> str | None:
        lower = waste_type.lower()
        for key, icon in ICON_MAP.items():
            if key in lower:
                return icon
        return None
