import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisDistinctValues,
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# "Property Waste Collection Days and Recycle Weeks" on the City of Moreton
# Bay open-data portal: each parcel carries its collection weekday (Bin_Day)
# and its recycling fortnight (Recycle_Week = "WEEK 1"/"WEEK 2").
_API_URL = (
    "https://services-ap1.arcgis.com/152ojN3Ts9H3cdtl/arcgis/rest/services/"
    "MBRC_Waste/FeatureServer/0"
)

# The Monday starting a council "WEEK 1" fortnight: 25 Pumicestone Street,
# Bellara (WEEK 1) had its recycling collected Thu 16 Jul 2026. Queensland has
# no daylight saving, so the fortnight parity holds all year.
_WEEK1_MONDAY = datetime.date(2026, 7, 13)
_WEEKS_AHEAD = 12


def _quoted(value) -> str:
    return str(value).strip().upper().replace("'", "''")


def _where(house_number, street, suburb, **_) -> str:
    return (
        f"House_No='{_quoted(house_number)}' "
        f"AND UPPER(Road) LIKE '%{_quoted(street)}%' "
        f"AND UPPER(Suburb)='{_quoted(suburb)}'"
    )


def _describe(record, source):
    """General waste weekly; recycling and garden organics on alternate weeks."""
    weekday = recurrence.weekday((record.get("Bin_Day") or "").strip())
    if weekday is None:
        return
    week1 = _WEEK1_MONDAY + datetime.timedelta(days=weekday)
    week2 = week1 + datetime.timedelta(weeks=1)
    recycling, garden = (
        (week1, week2)
        if (record.get("Recycle_Week") or "").strip().upper() == "WEEK 1"
        else (week2, week1)
    )
    yield Schedule("General Waste", week1, recurrence.WEEKLY, _WEEKS_AHEAD, anchor=True)
    for key, start in (("Recycling", recycling), ("Garden Organics", garden)):
        yield Schedule(
            key, start, recurrence.FORTNIGHTLY, _WEEKS_AHEAD // 2, anchor=True
        )


@final
class Source(BaseSource):
    TITLE = "City of Moreton Bay"
    DESCRIPTION = "Source for City of Moreton Bay, Queensland, Australia."
    URL = "https://www.moretonbay.qld.gov.au"
    COUNTRY = "au"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@CRZTFR"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GARDEN_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "25 Pumicestone Street, Bellara": {
            "house_number": "25",
            "street_name": "Pumicestone",
            "suburb": "Bellara",
        },
        "74 North Street, Woorim": {
            "house_number": 74,
            "street_name": "North Street",
            "suburb": "Woorim",
        },
        "8 Irene Street, Redcliffe": {
            "house_number": "8",
            "street_name": "Irene",
            "suburb": "Redcliffe",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown house number": {
            "house_number": "9999",
            "street_name": "Pumicestone",
            "suburb": "Bellara",
        },
    }

    PARAMS = (house_number(), street("street_name"), text_field("suburb", "Suburb"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your house number, street name and suburb exactly as they "
            "appear on the City of Moreton Bay bin-day lookup at "
            "https://www.moretonbay.qld.gov.au/Services/Waste-Recycling/Collections/Bin-Days. "
            "The street name may be given with or without its street type "
            "(e.g. 'Pumicestone' or 'Pumicestone Street')."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _API_URL,
        where=lambda house_number, street_name, suburb, **_: _where(
            house_number, street_name, suburb
        ),
        out_fields="ADDRESS,Bin_Day,Recycle_Week",
        # The units of one building share its schedule.
        result_record_count=1,
    )
    # An address the layer does not know is answered with the street's.
    parse = ArcGisFeatureParser(
        argument="house_number",
        suggestions=ArcGisDistinctValues(
            _API_URL,
            "ADDRESS",
            where=lambda street_name, suburb, **_: (
                f"UPPER(Road) LIKE '%{_quoted(street_name)}%' "
                f"AND UPPER(Suburb)='{_quoted(suburb)}'"
            ),
            limit=10,
        ),
    )
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Organics": wt.GARDEN_WASTE,
        }
    )
