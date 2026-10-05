from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://yokqi4ofx1.execute-api.ap-southeast-2.amazonaws.com/Live"


def _parcel_no(response, *, address: str, **_) -> str:
    """The parcel of the first matching address: ``[[address, parcel], ...]``."""
    matches = response.json()
    if not matches:
        raise SourceArgumentNotFound("address", address)
    return matches[0][1]["value"]


def _part(field: dict, index: int) -> str:
    """One part of "Thursday, 01 October 2026, Garbage and Recycling"."""
    return field["value"].split(", ")[index]


@final
class Source(BaseSource):
    TITLE = "Wollondilly Shire Council"
    DESCRIPTION = "Source for Wollondilly Shire Council."
    URL = "https://www.wollondilly.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "87 Remembrance Driveway TAHMOOR NSW": {
            "address": "87 Remembrance Driveway TAHMOOR NSW"
        },
        "Thirlmere Way THIRLMERE NSW": {"address": "Thirlmere Way THIRLMERE NSW"},
    }

    PARAMS = (street_address(),)

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{_API_URL}/wcc_address_lookup",
                params=lambda address, **_: {"fields": address},
                pick=_parcel_no,
            ),
        ),
        url=f"{_API_URL}/wcc_details_lookup",
        params=lambda parcel_no, **_: {"fields": parcel_no},
        raise_for_status=True,
    )
    # The property's fields; each "WasteNextPickup" one names a date and the
    # bins collected that day.
    parse = parsers.JsonParser(0)
    preprocess = RowFilter(lambda field, _source: "WasteNextPickup" in field["name"])
    transform = JsonTransformer(
        date_key=lambda field: _part(field, 1),
        type_key=lambda field: _part(field, 2),
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "Garbage and Recycling": [wt.GENERAL_WASTE, wt.RECYCLABLES],
            "Garbage and Garden Organics": [wt.GENERAL_WASTE, wt.GARDEN_WASTE],
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Organics": wt.GARDEN_WASTE,
        },
    )
