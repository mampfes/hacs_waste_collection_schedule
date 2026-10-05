from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisDistinctValues,
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_FEATURE_URL = (
    "https://services2.arcgis.com/ZASkNq1SMoPvFBOv/arcgis/rest/services"
    "/Marysville_Solid_Waste_Pickup/FeatureServer/29"
)
_WEEKS_AHEAD = 26


def _upper(street_address: str) -> str:
    return street_address.strip().upper().replace("'", "''")


def _describe(record, source):
    """Weekly, or every fourth week for a "Monthly" pickup, on the service day."""
    weekday = recurrence.weekday((record.get("Service_Day") or "").strip())
    if weekday is None:
        return
    start = recurrence.next_weekday(weekday)
    if (record.get("Pickup_Frequency") or "").strip() == "Monthly":
        yield Schedule(
            "Garbage Collection", start, recurrence.WEEKLY * 4, _WEEKS_AHEAD // 4
        )
    else:
        yield Schedule("Garbage Collection", start, recurrence.WEEKLY, _WEEKS_AHEAD)


@final
class Source(BaseSource):
    TITLE = "Marysville, WA"
    DESCRIPTION = "Source for Marysville, WA solid waste collection schedules."
    URL = "https://marysvillewa.gov/172/Solid-Waste-Recycling"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Marysville City Hall (501 Delta Ave) - Friday weekly": {
            "street_address": "501 Delta Ave"
        },
        "4011 81st Pl NE - Monday weekly": {"street_address": "4011 81st Pl NE"},
        "8507 61st Dr NE - Wednesday monthly": {"street_address": "8507 61st Dr NE"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"street_address": "9999 Delta Ave"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the house number and street name (e.g. '501 Delta Ave' or "
            "'6400 88th St NE'), without city or ZIP code."
        ),
    }

    # The service addresses are stored upper case; an address that matches
    # nothing is answered with the addresses containing it.
    retrieve = ArcGisFeatureRetriever(
        _FEATURE_URL,
        where=lambda street_address, **_: (
            f"UPPER(Service_Address) LIKE '{_upper(street_address)}%'"
        ),
        out_fields="Service_Address,Service_Day,Pickup_Frequency",
    )
    parse = ArcGisFeatureParser(
        argument="street_address",
        suggestions=ArcGisDistinctValues(
            _FEATURE_URL,
            "Service_Address",
            where=lambda street_address, **_: (
                f"UPPER(Service_Address) LIKE '%{_upper(street_address)}%'"
            ),
            limit=5,
        ),
    )
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map={"Garbage Collection": wt.GENERAL_WASTE})
