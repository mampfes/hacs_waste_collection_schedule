import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_PAGE_URL = "https://www.sysav.se/privat/min-sophamtning/"
_DATA_API = re.compile(r"data-api\s*=\s*\"([^\"]+)\"")
# "v40 tis 2026": ISO week, weekday name, year. Anything else is an ISO date.
_WEEK_DATE = re.compile(r"v(\d*)\s+\w+\s*(\d+)")


def _data_api(response, *keys, **_) -> str:
    """The API base URL the calendar page embeds as ``data-api``."""
    match = _DATA_API.search(response.text)
    if match is None:
        raise ValueError("Sysav page does not embed its data-api URL")
    return match.group(1)


def _building(response, *keys, street_address, **_) -> str:
    """The building id of the first address the search finds."""
    buildings = response.json()
    if not buildings:
        raise SourceArgumentNotFound("street_address", street_address)
    return buildings[0]


def _pickup_date(record) -> datetime.date:
    next_pickup = record["nextPickupDate"]
    week = _WEEK_DATE.match(next_pickup)
    if week:
        return datetime.date.fromisocalendar(
            year=int(week.group(2)), week=int(week.group(1)), day=1
        )
    return datetime.datetime.fromisoformat(next_pickup).date()


@final
class Source(BaseSource):
    TITLE = "Sysav Sophämntning"
    DESCRIPTION = "Source for Sysav waste collection."
    URL = "https://www.sysav.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GLASS,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Home": {"street_address": "Sommargatan 1, Svedala"},
        "Furulund": {"street_address": "Asagatan 2, Furulund"},
        "Käglinge": {"street_address": "Kvarngatan 13, Kävlinge"},
    }

    PARAMS = (street_address("street_address"),)

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(_PAGE_URL, pick=_data_api),
            Lookup(
                lambda api, street_address, **_: (
                    f"{api}/PickupSchedules/findbuilding/{street_address}"
                ),
                pick=_building,
            ),
        ),
        url=lambda api, building, **_: f"{api}/PickupSchedules/foraddress/{building}",
    )
    parse = JsonParser()
    transform = JsonTransformer(
        date_key=_pickup_date,
        type_key="wasteType",
        # "Kärl 1" / "Kärl 2" are Sysav's numbered two-bin rounds (residual and
        # food waste, respectively packaging and paper).
        type_value_map={
            "Kärl 1": wt.GENERAL_WASTE,
            "Kärl 2": wt.RECYCLABLES,
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Trädgårdsavfall": wt.GARDEN_WASTE,
            "Ofärgat Glas": wt.GLASS,
            "Färgat Glas": wt.GLASS,
            "Metallförp": wt.RECYCLABLES,
            "Plastförp": wt.RECYCLABLES,
            "Returpapper": wt.PAPER,
            "Pappersförp": wt.PAPER,
        },
    )
