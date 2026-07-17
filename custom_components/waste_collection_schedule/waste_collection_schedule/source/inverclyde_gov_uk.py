import re

from curl_cffi import requests
from dateutil.parser import parse as parse_date
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Inverclyde Council"
DESCRIPTION = "Source for Inverclyde Council, UK, waste collection."
URL = "https://www.inverclyde.gov.uk"
TEST_CASES = {
    "1 Findhorn Crescent": {"postcode": "PA16 0FG", "address": "1 Findhorn Crescent"},
    "1 Merrylee Avenue": {"postcode": "PA14 5UT", "address": "1 Merrylee Avenue"},
    "10 St John's Road": {"postcode": "PA19 1PL", "address": "10 St John's Road"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://maps.inverclyde.gov.uk/noticeboard8/noticeboard.aspx, "
    "search for your postcode and note down your address exactly as it is shown "
    "in the address list, e.g. '10 St John's Road'."
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "address": "Address",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "The postcode of the property, e.g. 'PA16 0FG'",
        "address": "The first line of the address exactly as returned by the "
        "council's address search, e.g. '10 St John's Road'",
    }
}

ICON_MAP = {
    "black": Icons.GENERAL_WASTE,
    "grey": Icons.GENERAL_WASTE,
    "food": Icons.BIO_KITCHEN,
    "blue": Icons.RECYCLING,
    "brown": Icons.GARDEN,
}

BIN_NAME_MAP = {
    "black": "General Waste",
    "grey": "General Waste",
    "food": "Food Waste",
    "blue": "Recycling",
    "brown": "Garden Waste",
}

API_BASE = "https://maps.inverclyde.gov.uk/noticeboard8"
QUICKSEARCH_URL = f"{API_BASE}/quicksearch.asmx/GetMoreResults"
LOCALKNOWLEDGE_URL = f"{API_BASE}/LocalKnowledge.asmx/AboutTheLocationForOverlay"

# IDs of the "Address Results" quick search and the "Bin Collections" overlay,
# as configured on the council's NoticeBoard map (maps.inverclyde.gov.uk).
ADDRESS_SEARCH_ID = 7
LOCAL_KNOWLEDGE_ID = 3
BIN_COLLECTIONS_OVERLAY_NO = 20

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{API_BASE}/noticeboard.aspx",
}

BIN_ALT_TEXT_PATTERN = re.compile(r'alt="Image of an? (\w+) bin"', re.IGNORECASE)
DATE_PATTERN = re.compile(r"[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)\s+[A-Za-z]+\s+\d{4}")


def _parse_date(text: str | None):
    if not text:
        return None
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    try:
        return parse_date(match.group(0), fuzzy=True).date()
    except (ValueError, OverflowError):
        return None


class Source:
    def __init__(self, postcode: str, address: str):
        self._postcode = postcode
        self._address = address

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        r = session.post(
            QUICKSEARCH_URL,
            headers=HEADERS,
            json={
                "searchId": ADDRESS_SEARCH_ID,
                "filter": self._postcode,
                "startIndex": 0,
                "endIndex": 199,
            },
        )
        r.raise_for_status()
        results = r.json().get("d", {}).get("Data") or []

        matched_columns = None
        suggestions = []
        for item in results:
            columns = {c["Name"]: c["Value"] for c in item.get("Columns", [])}
            address_text = columns.get("RESULTS", "")
            first_line = address_text.split("\r\n")[0].strip()
            suggestions.append(first_line)
            if first_line.lower() == self._address.strip().lower():
                matched_columns = columns
                break

        if matched_columns is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, suggestions
            )

        r = session.post(
            LOCALKNOWLEDGE_URL,
            headers=HEADERS,
            json={
                "localKnowledgeID": LOCAL_KNOWLEDGE_ID,
                "overlayNo": BIN_COLLECTIONS_OVERLAY_NO,
                "x": matched_columns["E"],
                "y": matched_columns["N"],
            },
        )
        r.raise_for_status()
        data = r.json().get("d") or {}

        attributes: dict[str, str] = {}
        for fmn in data.get("FMNResults") or []:
            for item in fmn.get("Items") or []:
                for attr in item.get("Attributes") or []:
                    attributes[attr["Name"]] = attr.get("Value", "")

        entries: list[Collection] = []
        for date_key, graphic_key in (
            ("top_bin_date2", "top_bin_graphic"),
            ("bottom_bin_date2", "bottom_bin_graphic"),
        ):
            date = _parse_date(attributes.get(date_key))
            if date is None:
                continue

            graphic = attributes.get(graphic_key, "")
            colours = BIN_ALT_TEXT_PATTERN.findall(graphic)
            for colour in colours:
                colour = colour.lower()
                name = BIN_NAME_MAP.get(colour, f"{colour.title()} Bin")
                entries.append(Collection(date, name, ICON_MAP.get(colour)))

        return entries
