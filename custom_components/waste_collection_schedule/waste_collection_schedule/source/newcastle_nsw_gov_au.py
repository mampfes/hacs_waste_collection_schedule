import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# ArcGis single spatial query -> one feature with Day + WeekNo, from which three
# recurring schedules are projected (general weekly; recycling/green fortnightly
# on opposite weeks). Acquisition + parse are the shared ArcGis components; the
# only source-specific code is _describe (the council's week/anchor logic).

FEATURE_URL = "https://services-ap1.arcgis.com/CNeUPE1voVc22gNk/arcgis/rest/services/WasteCollectionDay/FeatureServer/0"

_TYPE_MAP = {
    "General Waste": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
    "Green Waste": GARDEN_WASTE,
}

# Reference date for the fortnightly cycle (from the ArcGIS Arcade expression).
# 28 Jun 2021 is week 0 -> CalWk=2 (even).
EPOCH = datetime.date(2021, 6, 28)


def _base_date_for_week(weekday: int, week_no: int) -> datetime.date:
    """Reference date for ``weekday`` falling in the requested CalWk (1 or 2)."""
    candidate = EPOCH + datetime.timedelta(days=(weekday - EPOCH.weekday()) % 7)
    week_index = (candidate - EPOCH).days // 7
    cal_wk = 2 if week_index % 2 == 0 else 1
    if cal_wk != week_no:
        candidate += datetime.timedelta(days=7)
    return candidate


def _describe(attrs, source):
    day = (attrs.get("Day") or "").strip()
    week_no = attrs.get("WeekNo")
    weekday = recurrence.weekday(day)
    if weekday is None or week_no not in (1, 2):
        return

    # General Waste (red lid) — weekly.
    yield Schedule(
        "General Waste", recurrence.next_weekday(weekday), recurrence.WEEKLY, 26
    )

    # Recycling (yellow lid) — fortnightly on matching weeks.
    recycling_base = _base_date_for_week(weekday, week_no)
    yield Schedule("Recycling", recycling_base, recurrence.FORTNIGHTLY, 13, anchor=True)

    # Green Waste (green lid) — fortnightly on the opposite week.
    yield Schedule(
        "Green Waste",
        recycling_base + datetime.timedelta(days=7),
        recurrence.FORTNIGHTLY,
        13,
        anchor=True,
    )


@final
class Source(BaseSource):
    TITLE = "City of Newcastle"
    DESCRIPTION = "Source for City of Newcastle (NSW) waste collection."
    URL = "https://www.newcastle.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "King Street": {"address": "1 King Street, Newcastle NSW 2300"},
        "Stockton": {"address": "5 Pacific Street, Stockton NSW 2295"},
        "Waratah": {"address": "30 Turton Road, Waratah NSW 2298"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address within the City of Newcastle "
            "(e.g. '1 King Street, Newcastle NSW 2300')."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL, address="address", out_fields="WeekNo,Day"
    )
    parse = ArcGisFeatureParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
