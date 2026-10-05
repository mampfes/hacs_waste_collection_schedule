import datetime
import json
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

ADDRESS_SEARCH_URL = (
    "https://www.cairns.qld.gov.au/_external/my-property/address-search"
)
PROPERTY_SEARCH_URL = (
    "https://www.cairns.qld.gov.au/property-and-business/property-search"
)

_PROPERTY_DATA_RE = re.compile(r"var PropertyData = (\{.*?\});", re.DOTALL)

_TYPE_MAP = {
    "General Waste": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
}

# Number of future occurrences to generate for each waste type.
_WASTE_WEEKS_AHEAD = 52
_RECYCLE_FORTNIGHTS_AHEAD = 26

# The API gives only the next recycling date, as "Thu 23 July" (no year).
_RECYCLE_DATE = date_parsers.next_weekday("%d %B")


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower().rstrip(",")


def _pick_address_id(response, *keys, address, **_) -> str:
    """The address search answers a list of ``{addressId, streetAddress, suburb}``."""
    results = response.json()
    if not results:
        raise SourceArgumentNotFound("address", address)

    labels = [f"{item['streetAddress']}, {item['suburb']}" for item in results]
    wanted = _normalise(address)
    for item, label in zip(results, labels, strict=True):
        if _normalise(label) == wanted:
            return str(item["addressId"])

    if len(results) == 1:
        return str(results[0]["addressId"])

    raise SourceArgumentNotFoundWithSuggestions("address", address, labels[:15])


def _bin_data(page: str, source) -> list[dict]:
    """The property page embeds ``var PropertyData = {..., "binData": {...}};``."""
    match = _PROPERTY_DATA_RE.search(page)
    if not match:
        raise ValueError(
            "Could not find property data on the Cairns Regional Council "
            "website. The page layout may have changed."
        )
    bin_data = json.loads(match.group(1)).get("binData")
    if not bin_data:
        raise ValueError(
            f"No bin collection data found for address '{source.params['address']}'."
        )
    return [bin_data]


def _describe(bin_data: dict, source):
    """General waste is weekly, recycling fortnightly, from the next date given."""
    waste_date = bin_data.get("runDateWaste")
    if waste_date:
        yield Schedule(
            "General Waste",
            datetime.date.fromisoformat(waste_date.split("T")[0]),
            recurrence.WEEKLY,
            _WASTE_WEEKS_AHEAD,
        )

    recycle_date = bin_data.get("runDateRecycle")
    if recycle_date:
        yield Schedule(
            "Recycling",
            _RECYCLE_DATE(" ".join(recycle_date.split()[-2:])),
            recurrence.FORTNIGHTLY,
            _RECYCLE_FORTNIGHTS_AHEAD,
        )


@final
class Source(BaseSource):
    TITLE = "Cairns Regional Council"
    DESCRIPTION = "Source for Cairns Regional Council, QLD, Australia."
    URL = "https://www.cairns.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "7 Keats Close, Mount Sheridan": {"address": "7 Keats Close, MOUNT SHERIDAN"},
        "1 Abington Close, Redlynch": {"address": "1 Abington Close, Redlynch"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to the Cairns Regional Council "
            "[Find my bin day](https://www.cairns.qld.gov.au/water-waste-roads/waste-and-recycling/bin-collection/find-bin-day) "
            "page, start typing your address and pick it from the autocomplete "
            "list. Use the same 'STREET NUMBER STREET NAME, SUBURB' format shown "
            "in the suggestion for the `address` argument."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                ADDRESS_SEARCH_URL,
                params=lambda address, **_: {"search": address},
                pick=_pick_address_id,
            ),
        ),
        url=PROPERTY_SEARCH_URL,
        params=lambda key, **_: {"address-id": key},
    )

    parse = parsers.TextParser()

    preprocess = Compose(_bin_data, RecurrenceExpander(_describe))

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
