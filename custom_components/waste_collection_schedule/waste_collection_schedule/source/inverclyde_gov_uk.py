import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import Lookup, Request
from waste_collection_schedule.transformers import JsonTransformer

_API_BASE = "https://maps.inverclyde.gov.uk/noticeboard8"

# IDs of the "Address Results" quick search and the "Bin Collections" overlay,
# as configured on the council's NoticeBoard map (maps.inverclyde.gov.uk).
_ADDRESS_SEARCH_ID = 7
_LOCAL_KNOWLEDGE_ID = 3
_BIN_COLLECTIONS_OVERLAY_NO = 20

_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{_API_BASE}/noticeboard.aspx",
}

_BIN_ALT_TEXT = re.compile(r'alt="Image of an? (\w+) bin"', re.IGNORECASE)
_DATE = re.compile(r"[A-Za-z]+\s+(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z]+)\s+(\d{4})")


def _location(response, *, address: str, **_) -> tuple:
    """The (easting, northing) of the address whose first line matches."""
    results = response.json().get("d", {}).get("Data") or []
    suggestions = []
    for item in results:
        columns = {c["Name"]: c["Value"] for c in item.get("Columns", [])}
        first_line = columns.get("RESULTS", "").split("\r\n")[0].strip()
        suggestions.append(first_line)
        if first_line.lower() == address.strip().lower():
            return columns["E"], columns["N"]
    raise SourceArgumentNotFoundWithSuggestions("address", address, suggestions)


def _bins(record, source) -> list:
    """One record per bin colour shown for each of the two upcoming dates."""
    attributes = {
        attr["Name"]: attr.get("Value", "")
        for item in record.get("Items") or []
        for attr in item.get("Attributes") or []
    }
    rows = []
    for date_key, graphic_key in (
        ("top_bin_date2", "top_bin_graphic"),
        ("bottom_bin_date2", "bottom_bin_graphic"),
    ):
        found = _DATE.search(attributes.get(date_key) or "")
        if not found:
            continue
        date = " ".join(found.groups())
        for colour in _BIN_ALT_TEXT.findall(attributes.get(graphic_key) or ""):
            rows.append({"date": date, "colour": colour.lower()})
    return rows


@final
class Source(BaseSource):
    TITLE = "Inverclyde Council"
    DESCRIPTION = "Source for Inverclyde Council, UK, waste collection."
    URL = "https://www.inverclyde.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "1 Findhorn Crescent": {
            "postcode": "PA16 0FG",
            "address": "1 Findhorn Crescent",
        },
        "1 Merrylee Avenue": {"postcode": "PA14 5UT", "address": "1 Merrylee Avenue"},
        "10 St John's Road": {"postcode": "PA19 1PL", "address": "10 St John's Road"},
    }

    PARAMS = (postcode(), street_address("address"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://maps.inverclyde.gov.uk/noticeboard8/noticeboard.aspx, "
            "search for your postcode and note down your address exactly as it is "
            "shown in the address list, e.g. '10 St John's Road'."
        ),
    }

    # The address search gives the property's map coordinates, which the
    # "Bin Collections" overlay is then queried at.
    retrieve = Request(
        f"{_API_BASE}/LocalKnowledge.asmx/AboutTheLocationForOverlay",
        method="POST",
        headers=_HEADERS,
        json=lambda location, **_: {
            "localKnowledgeID": _LOCAL_KNOWLEDGE_ID,
            "overlayNo": _BIN_COLLECTIONS_OVERLAY_NO,
            "x": location[0],
            "y": location[1],
        },
        before=(
            Lookup(
                f"{_API_BASE}/quicksearch.asmx/GetMoreResults",
                method="POST",
                headers=_HEADERS,
                json=lambda postcode, **_: {
                    "searchId": _ADDRESS_SEARCH_ID,
                    "filter": postcode,
                    "startIndex": 0,
                    "endIndex": 199,
                },
                pick=_location,
            ),
        ),
    )

    parse = JsonParser("d", "FMNResults")

    preprocess = ExplodeList(_bins)

    transform = JsonTransformer(
        date_key="date",
        type_key="colour",
        type_value_map={
            "black": wt.GENERAL_WASTE,
            "grey": wt.GENERAL_WASTE,
            "food": wt.FOOD_WASTE,
            "blue": wt.RECYCLABLES,
            "brown": wt.GARDEN_WASTE,
        },
    )
