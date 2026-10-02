import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.transformers import ICSTransformer

API = "https://mapping.manningham.vic.gov.au/weave/services/v1"

# The mapping server answers XML unless told otherwise.
JSON_HEADERS = {"Accept": "application/json"}

# Collections are projected one year ahead.
HORIZON = datetime.timedelta(days=365)

_NEXT_DATE = date_parsers.for_format("%d %b %Y")
_NEXT_WEEKDAY = date_parsers.next_weekday()


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _pick_property_id(response, *keys, street_address, **_) -> str:
    """The index search answers ``{"total": n, "results": [{"id", "display1"}]}``."""
    found = response.json()
    if not found.get("total"):
        raise SourceArgumentNotFound("street_address", street_address)
    if found["total"] > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "street_address",
            street_address,
            [_strip_html(r["display1"]) for r in found["results"]],
        )
    return found["results"][0]["id"]


def _describe(feature, source):
    """Rubbish and recycling fortnightly from their next date, garden waste weekly."""
    rows = feature.get("properties", {}).get("dd_ManCC_Property_WasteCollection")
    if not rows:
        return
    data = rows[0]
    until = datetime.date.today() + HORIZON

    for key, field in (
        ("Rubbish", "ManCC_Collection_Day"),
        ("Recycling", "ManCC_Recycling_Day"),
    ):
        if data.get(field):
            yield Schedule(
                key,
                _NEXT_DATE(data[field]),
                recurrence.FORTNIGHTLY,
                until=until,
            )

    if data.get("ManCC_Garden_Waste_Day"):
        yield Schedule(
            "Garden Waste",
            _NEXT_WEEKDAY(data["ManCC_Garden_Waste_Day"]),
            recurrence.WEEKLY,
            until=until,
        )


@final
class Source(BaseSource):
    TITLE = "City of Manningham"
    DESCRIPTION = "Source for City of Manningham, Victoria, Australia waste collection."
    URL = "https://www.manningham.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "10 Harold Street Bulleen": {"street_address": "10 Harold Street"},
        "Lower Templestowe Pre-School": {"street_address": "96-106 Swanston Street"},
        "9/114-116 James Street Templestowe": {
            "street_address": "9/114-116 James Street"
        },
        "488 Park Road Park Orchards": {"street_address": "488 Park Road"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address within the City of Manningham, e.g. "
            "'10 Harold Street'. It must match exactly one property; if several "
            "match, the error lists the candidates."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/index/search",
                params=lambda street_address, **_: {
                    "start": "0",
                    "limit": "10",
                    "indexes": "index.ManCC_propertylayer",
                    "type": "EXACT",
                    "crs": "EPSG:28355",
                    "query": street_address,
                },
                headers=JSON_HEADERS,
                pick=_pick_property_id,
            ),
        ),
        url=f"{API}/feature/getFeaturesByIds",
        params=lambda property_id, **_: [
            ("outCrs", "EPSG:28355"),
            ("datadefinition", "dd_ManCC_prop_layer_index"),
            ("datadefinition", "dd_ManCC_Property_WasteCollection"),
            ("entityId", "ManCC_prop_layer"),
            ("ids", property_id),
        ],
        headers=JSON_HEADERS,
        raise_for_status=True,
    )

    parse = parsers.JsonParser("features")

    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
