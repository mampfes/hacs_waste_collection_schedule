import datetime
from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_ZONE_URL = "https://services9.arcgis.com/CsUMpO9iTKFFwe1O/arcgis/rest/services/Waste_View_Public/FeatureServer/4"

# Sunday 5 Jan 2025 starts a "Week A"; zone A recycles in week A, and organics
# go out on the other week. General waste is weekly.
_WEEK_A_SUNDAY = datetime.date(2025, 1, 5)
_WEEKS_AHEAD = 26

# The council's own list of days on which collection moves to the next day
# (from its bin-day page's functions.js).
_HOLIDAYS = {
    date(2025, 1, 1),
    date(2025, 1, 2),
    date(2025, 1, 3),
    date(2025, 4, 18),
    date(2025, 12, 25),
    date(2025, 12, 26),
    date(2026, 1, 1),
    date(2026, 1, 2),
    date(2026, 4, 3),
    date(2026, 12, 25),
    date(2027, 1, 1),
    date(2027, 3, 26),
    date(2027, 12, 25),
    date(2028, 1, 1),
    date(2028, 4, 14),
    date(2028, 12, 25),
    date(2028, 12, 26),
    date(2028, 12, 27),
    date(2028, 12, 28),
    date(2028, 12, 29),
}


def _describe(record, source):
    weekday = recurrence.weekday((record.get("Collection") or "").strip())
    if weekday is None:
        return
    week_a = _WEEK_A_SUNDAY + datetime.timedelta(days=(weekday + 1) % 7)
    week_b = week_a + datetime.timedelta(weeks=1)
    recycling, organics = (
        (week_a, week_b) if record.get("Week") == "A" else (week_b, week_a)
    )
    fortnights = _WEEKS_AHEAD // 2
    yield Schedule(
        "General Waste", week_a, recurrence.WEEKLY, _WEEKS_AHEAD, anchor=True
    )
    yield Schedule(
        "Recycling", recycling, recurrence.FORTNIGHTLY, fortnights, anchor=True
    )
    yield Schedule(
        "Organics", organics, recurrence.FORTNIGHTLY, fortnights, anchor=True
    )


def _after_holiday(collection_date, key, source):
    return collection_date + datetime.timedelta(
        days=1 if collection_date in _HOLIDAYS else 0
    )


@final
class Source(BaseSource):
    TITLE = "City of Tea Tree Gully"
    DESCRIPTION = "Source for City of Tea Tree Gully waste collection."
    URL = "https://www.teatreegully.sa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Erica Street": {"address": "4 Erica Street, Tea Tree Gully"},
        "Smart Road": {"address": "1 Smart Road, Modbury"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address with suburb (e.g. '4 Erica Street, Tea "
            "Tree Gully'). Search at "
            "https://www.teatreegully.sa.gov.au/services/bins-and-waste/bin-collection-days"
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _ZONE_URL,
        address=lambda address, **_: f"{address}, South Australia",
        out_fields="Collection,Week",
        result_record_count=1,
    )
    parse = ArcGisFeatureParser(argument="address")
    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_after_holiday))
    transform = ICSTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Organics": wt.ORGANIC,
        }
    )
