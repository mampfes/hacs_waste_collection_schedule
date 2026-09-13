import re
from datetime import date, datetime

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "City of Gosnells"
DESCRIPTION = "Source for City of Gosnells, Western Australia."
URL = "https://www.gosnells.wa.gov.au/"
TEST_CASES = {
    "Test_001": {"address": "15 Mackay Crescent GOSNELLS 6110"},
    "Test_002": {"address": "7 Darkin Drive GOSNELLS 6110"},
    "Test_003": {"address": "35 Prince Street GOSNELLS 6110"},
    "Test_004 (space character test)": {"address": "4A Turley Court LANGFORD 6147"},
}

PAGE_URL = "https://www.gosnells.wa.gov.au/City-Services/Waste-and-Recycling/Find-your-waste-collection-dates"

HEADERS = {
    "user-agent": "Mozilla/5.0",
    # Without an explicit Accept header the search endpoint returns XML
    # instead of JSON.
    "accept": "application/json, text/javascript, */*; q=0.01",
    "x-requested-with": "XMLHttpRequest",
    "referer": PAGE_URL,
}

# Council service name (the h3 in the widget) mapped to the collection type
# reported to Home Assistant. The names on the right preserve the types this
# source emitted before the council moved to the OpenCities MyArea platform,
# so existing dashboards and automations keep working.
TYPE_MAP = {
    "general waste": "Rubbish",
    "recycling": "Recycling",
    "green waste": "Green",
    "bulk junk": "Junk",
}

ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green": Icons.ORGANIC,
    "Junk": Icons.ELECTRONICS,
}

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": f"Use the [City of Gosnells]({PAGE_URL}) website and search for your collection schedule. Use your address as it is displayed on the search results page.",
}
PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your street name and house number as it appears on the City of Gosnells website",
    },
}
PARAM_TRANSLATIONS = {
    "en": {
        "address": "Your street name and house number as it appears on the City of Gosnells website"
    },
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.gosnells.wa.gov.au",
    argument_name="address",
    headers=HEADERS,
    # The council sits behind Akamai, which rejects the TLS handshake plain
    # requests/urllib3 produces and answers 403 before the request reaches
    # the application.
    use_curl_cffi=True,
)

# "Mon 7/9/2026"
_PRECISE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
# "5th Oct - 13th Oct."
_APPROX_RE = re.compile(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,})", re.IGNORECASE)
_YEAR_RE = re.compile(r"(20\d{2})")


def _candidate_years(note: str, today: date) -> list[int]:
    """Years the note could be referring to.

    A note naming one year ("Verge Collection 2026") is taken at its word, even
    if that collection has already been and gone: verge collection weeks move
    from year to year, so rolling a past date forward would invent a date the
    council has not published. Only a note naming a span ("Verge Collection
    2026-2027") or naming no year at all leaves a real choice to make.
    """
    years = [int(y) for y in _YEAR_RE.findall(note)]
    if not years:
        years = [today.year, today.year + 1]
    return sorted(set(years))


def _parse_date(next_service: str, note: str, today: date) -> date | None:
    """Return the start date of a service's next collection."""
    match = _PRECISE_RE.search(next_service)
    if match:
        try:
            return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        except ValueError:
            return None

    # Verge collections give an approximate window instead, e.g.
    # "5th Oct - 13th Oct." The year appears only in the note ("Verge
    # Collection 2026-2027"), so try each year the note names and take the
    # first occurrence that has not already passed.
    match = _APPROX_RE.search(next_service)
    if not match:
        return None
    day = int(match.group(1))
    month = MONTHS.get(match.group(2)[:3].lower())
    if month is None:
        return None

    candidates = []
    for year in _candidate_years(note, today):
        try:
            candidates.append(date(year, month, day))
        except ValueError:
            continue
    future = [d for d in candidates if d >= today]
    if future:
        return min(future)
    return max(candidates) if candidates else None


class Source:
    def __init__(self, address: str):
        self._address = address
        self._client = OpenCitiesClient(_CONFIG)
        self._geolocation_id: str | None = None

    def fetch(self) -> list[Collection]:
        # Gosnells reports its verge collections as an approximate window
        # ("5th Oct - 13th Oct.") whose year lives in the block's "note" div,
        # which the shared client's parser doesn't return, so parse the raw
        # HTML locally.
        if self._geolocation_id is None:
            self._geolocation_id = self._client.resolve_geolocation_id(self._address)
        html = self._client.get_waste_services_html(self._geolocation_id)
        soup = BeautifulSoup(html, "html.parser")

        today = datetime.now().date()
        entries: list[Collection] = []
        for block in soup.find_all("div", attrs={"class": "waste-services-result"}):
            title = block.find("h3")
            next_service = block.find("div", attrs={"class": "next-service"})
            if title is None or next_service is None:
                continue

            note = block.find("div", attrs={"class": "note"})
            note_text = note.get_text(" ", strip=True) if note else ""

            collection_date = _parse_date(
                next_service.get_text(" ", strip=True), note_text, today
            )
            if collection_date is None:
                continue

            # "Green Waste 1" and "Green Waste 2" are the two verge collections.
            name = title.get_text(" ", strip=True)
            key = re.sub(r"\s*\d+$", "", name).strip().lower()
            waste_type = TYPE_MAP.get(key, name)

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
