import datetime
from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.transformers import ICSTransformer

SEARCH_URL = (
    "https://data.napier.govt.nz/regional/shared/widgets/propertysearch/do_search.php"
)
API_URL = "https://data.napier.govt.nz/regional/ncc/widgets/collectiondays/do_collectiondays.php"

_TYPE_MAP = {
    "Rubbish": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
}

# The legacy source reported the past 7 and the next 7 occurrences of each weekday.
_WEEKS_BEFORE = 7
_OCCURRENCES = 15


class _Property(NamedTuple):
    valuation_id: str
    sufi_id: str
    ra_unique_id: str


def _pick_property(response, *keys, address, **_) -> _Property:
    """The search answers a list of ``{id, valuation_id, sufi_id, ra_unique_id, value}``."""
    hits = response.json()
    if not hits or hits[0].get("id") == "0":
        raise SourceArgumentNotFound("address", address)
    if len(hits) > 1:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, [hit["value"] for hit in hits]
        )
    hit = hits[0]
    return _Property(hit["valuation_id"], hit["sufi_id"], hit["ra_unique_id"])


def _describe(table, source):
    """One table per service: a header "Rubbish collection", a row "Every Monday - Out by 7am"."""
    header = table.find("th")
    if header is None:
        return
    label = header.get_text(strip=True).removesuffix(" collection").capitalize()
    for cell in table.find_all("td"):
        words = cell.get_text(strip=True).split(" ")
        if words[0] != "Every" or len(words) < 2:
            continue
        weekday = recurrence.weekday(words[1])
        if weekday is None:
            continue
        start = recurrence.next_weekday(weekday) - datetime.timedelta(
            weeks=_WEEKS_BEFORE
        )
        yield Schedule(label, start, recurrence.WEEKLY, _OCCURRENCES)


@final
class Source(BaseSource):
    TITLE = "Napier City Council"
    DESCRIPTION = "Source for Napier City Council"
    URL = "https://www.napier.govt.nz/"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"address": "4 Sheehan Street"},
        "Test2": {"address": "25 Bedford Road"},
        "Test3": {"address": "603 Marine Parade"},
        "Test4": {"address": "14 Cobden Road"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as it appears on the "
            "[Napier City Council website](https://www.napier.govt.nz/services/properties-and-rates/my-property/), "
            "e.g. '4 Sheehan Street'. The address must match a single property."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                SEARCH_URL,
                params=lambda address, **_: {
                    "search": address,
                    "council": "shared",
                    "type": "address",
                },
                pick=_pick_property,
            ),
        ),
        url=API_URL,
        params=lambda key, **_: {
            "v": key.valuation_id,
            "s": key.sufi_id,
            "r": key.ra_unique_id,
        },
    )

    parse = parsers.HtmlParser("table", from_json_key="html")

    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
