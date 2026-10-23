from datetime import date, timedelta
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
    ArcGisDistinctValues,
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# Public ArcGIS layer behind the council's bin day lookup. It only gives each
# property its collection day ("Day", or "NewDay" after a round change) and its
# collection area ("Week" 1 or 2); there are no dates.
FEATURE_URL = (
    "https://services3.arcgis.com/lfHi3I35DWultHqw/arcgis/rest/services/"
    "BinCollectionData/FeatureServer/0"
)

# Garbage is weekly; recycling and green waste alternate weekly, with the two
# areas in opposite phase. Per the council's 2026/27 Waste and Recycling
# Calendar, the week starting Monday 19 October 2026 is a recycling week for
# area 1 and a green waste week for area 2.
RECYCLING_WEEK_AREA_1 = date(2026, 10, 19)

WEEKS = 26


def _address(street_address: str) -> str:
    """The layer's EZI_ADD form: upper case, single spaces, quoted for SQL."""
    return " ".join(street_address.upper().split()).replace("'", "''")


def _where(street_address, **_) -> str:
    return f"EZI_ADD = '{_address(street_address)}'"


def _similar(street_address, **_) -> str:
    """Addresses with the same number and street name, as suggestions."""
    prefix = " ".join(_address(street_address).split()[:2])
    return f"EZI_ADD LIKE '{prefix}%'"


def _describe(record, source):
    day = recurrence.weekday((record.get("NewDay") or record.get("Day") or "").strip())
    area = record.get("Week")
    if day is None or area not in (1, 2):
        return

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    first = monday + timedelta(days=day)
    recycling_now = (monday - RECYCLING_WEEK_AREA_1).days // 7 % 2 == 0
    if area == 2:
        recycling_now = not recycling_now
    later = first + recurrence.WEEKLY

    yield Schedule("Garbage", first, recurrence.WEEKLY, WEEKS)
    yield Schedule(
        "Recycling",
        first if recycling_now else later,
        recurrence.FORTNIGHTLY,
        WEEKS // 2,
    )
    yield Schedule(
        "Green Waste",
        later if recycling_now else first,
        recurrence.FORTNIGHTLY,
        WEEKS // 2,
    )


def _after_holiday(collection_date: date, key, source) -> date:
    """Christmas Day, New Year's Day and Good Friday collections move one day later."""
    if (collection_date.month, collection_date.day) in (
        (12, 25),
        (1, 1),
    ) or collection_date == recurrence.good_friday(collection_date.year):
        return collection_date + timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "Wyndham City Council, Melbourne"
    DESCRIPTION = "Source for Wyndham City Council rubbish collection."
    URL = "https://wyndham.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Truganina South Primary School": {
            "street_address": "3-19 Parkvista Drive TRUGANINA 3029"
        },
        "Westbourne Grammar School": {
            "street_address": "300 Sayers Road TRUGANINA 3029"
        },
        "Werribee Mercy Hospital": {
            "street_address": "300-310 Princes Highway WERRIBEE 3030"
        },
        "Wyndham Park Primary School": {
            "street_address": "59-77 Kookaburra Avenue WERRIBEE 3030"
        },
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as the council's bin day lookup on "
            "https://www.wyndham.vic.gov.au shows it, e.g. "
            "'3-19 Parkvista Drive TRUGANINA 3029'. An unknown address lists "
            "similar ones."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL,
        where=_where,
        out_fields="EZI_ADD,Day,NewDay,Week",
        result_record_count=1,
    )
    parse = ArcGisFeatureParser(
        argument="street_address",
        suggestions=ArcGisDistinctValues(
            FEATURE_URL, "EZI_ADD", where=_similar, limit=20
        ),
    )
    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_after_holiday))

    transform = ICSTransformer(
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Green Waste": wt.GARDEN_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
