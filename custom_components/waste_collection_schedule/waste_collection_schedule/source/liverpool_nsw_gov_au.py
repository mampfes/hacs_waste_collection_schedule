import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

API_URL = "https://data.liverpool.nsw.gov.au/api/explore/v2.1/catalog/datasets/bin-collection-days/records"

# (field prefix, label): the dataset holds, per bin, the first collection date
# (``<prefix>_week1``) and the interval in days (``<prefix>_schedule``).
BIN_TYPES = (
    ("garbagebin", "Garbage"),
    ("recyclebin", "Recycling"),
    ("organicbin", "Organic"),
)


def _pick_address(response: Any, address: str, **_: Any) -> str:
    """Resolve the typed address to the dataset's single matching ``gisaddress``."""
    data = response.json()
    if data["total_count"] == 0:
        raise SourceArgumentNotFound("address", address)
    addresses = [record["gisaddress"] for record in data["results"]]
    if data["total_count"] == 1:
        return addresses[0]
    raise SourceArgumentNotFoundWithSuggestions("address", address, addresses)


def _describe(record: Any, source: Any) -> Any:
    """One recurring Schedule per bin, from its first date and interval."""
    end_date = datetime.date.today() + datetime.timedelta(days=365)
    for prefix, label in BIN_TYPES:
        first = record.get(f"{prefix}_week1")
        if not first:
            continue
        start = datetime.date.fromisoformat(first)
        interval = record.get(f"{prefix}_schedule") or 7
        yield Schedule(label, start, datetime.timedelta(days=interval), until=end_date)


@final
class Source(BaseSource):
    TITLE = "Liverpool City Council (NSW)"
    DESCRIPTION = "Source for Liverpool City Council (NSW, Australia)"
    URL = "https://www.liverpool.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Carnes Hill": {
            "address": "600 Kurrajong Road, Carnes Hill, NSW 2171",
        },
    }

    PARAMS = (street_address(),)

    WASTE_TYPES = (wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as listed in the Liverpool City Council open "
            "data set, e.g. '600 Kurrajong Road, Carnes Hill, NSW 2171'."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                API_URL,
                params=lambda address, **_: {
                    "where": f'gisaddress like "{address}"',
                    "limit": 100,
                },
                pick=_pick_address,
            ),
        ),
        url=API_URL,
        params=lambda matched, **_: {
            "where": f'gisaddress = "{matched}"',
            "limit": 1,
        },
    )
    parse = JsonParser("results")
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Organic": wt.ORGANIC,
        }
    )
