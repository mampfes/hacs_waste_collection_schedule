import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    DateFields,
    ExplodeList,
    WeekdayRecurrence,
)
from waste_collection_schedule.transformers import ICSTransformer

API = "https://map.whitehorse.vic.gov.au/weave/services/v1"

_HTML_TAG = re.compile(r"</?.*?>")
_JSON = {"Accept": "application/json"}

_parse_next = date_parsers.for_format("%d %b %Y")


def _pick_property(response, *keys, street_address, **_) -> str:
    """One hit is taken as is; several must include the exact address."""
    results = response.json().get("results") or []
    if not results:
        raise SourceArgumentNotFound("street_address", street_address)
    if len(results) == 1:
        return results[0]["id"]
    wanted = street_address.lower().strip()
    for result in results:
        if _HTML_TAG.sub("", result["display1"]).lower().strip() == wanted:
            return result["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_address", street_address, [r["display1"] for r in results]
    )


def _waste_maps(record, source) -> list[dict]:
    return (record.get("properties") or {}).get("dd_whm_property_waste") or []


def _date(value):
    """A ``"12 Aug 2024"`` text, or ``None`` for one that is not a date."""
    try:
        return _parse_next(value)
    except ValueError:
        return None


_NEXT_DATES = DateFields(
    fields={"nextRecycle": "Recycle", "nextGOBS": "GOBS"}, parse_date=_date
)
_WEEKLY_HOUSEHOLD = WeekdayRecurrence(day="collectionDay", keys="Household", count=10)


def _rows(records, source):
    """The dated bins, then the weekly household bin projected from its weekday."""
    records = list(records)
    yield from _NEXT_DATES(records, source)
    yield from _WEEKLY_HOUSEHOLD(records, source)


@final
class Source(BaseSource):
    TITLE = "Whitehorse City Council"
    DESCRIPTION = "Source for Whitehorse City Council rubbish collection."
    URL = "https://www.whitehorse.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "17 Main Street BLACKBURN": {"street_address": "17 Main Street BLACKBURN"},
        "6/16 Ashted Road": {"street_address": "6/16 Ashted Road"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as the council's "
            "[map](https://map.whitehorse.vic.gov.au) property search lists it, "
            "e.g. '17 Main Street BLACKBURN'. If several properties match, the "
            "address must match one of them exactly."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/index/search",
                params=lambda street_address, **_: {
                    "start": 0,
                    "limit": 1000,
                    "indexes": "index.property",
                    "type": "EXACT",
                    "crs": "EPSG:3857",
                    "query": street_address.lower().strip(),
                },
                headers=_JSON,
                pick=_pick_property,
            ),
        ),
        url=f"{API}/feature/getFeaturesByIds",
        params=lambda property_id, **_: {
            "entityId": "lyr_vicmap_property",
            "datadefinition": "dd_whm_property_waste",
            "ids": property_id,
            "outCrs": "EPSG:3857",
            "returnCentroid": "false",
        },
        headers=_JSON,
    )

    parse = parsers.JsonParser("features")

    preprocess = Compose(ExplodeList(_waste_maps), _rows)

    transform = ICSTransformer(
        type_value_map={
            "Household": wt.GENERAL_WASTE,
            "GOBS": wt.GARDEN_WASTE,
            "Recycle": wt.RECYCLABLES,
        },
    )
