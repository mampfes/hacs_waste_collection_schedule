"""City of Philadelphia, PA.

Composes: :mod:`~waste_collection_schedule.service.PhilaGov` (the city's AIS
address index and its published observed-holiday calendar) with
:class:`~waste_collection_schedule.preprocessors.RecurrenceExpander`. AIS gives
the weekdays a property's rounds are collected on and nothing else, so the year
is projected weekly from them; the city's own holiday feed then slides whatever
lands after a holiday, and two collections pushed onto one day collapse in the
:class:`~waste_collection_schedule.preprocessors.Deduplicate`.
"""

from datetime import date
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.PhilaGov import (
    ADDRESS_URL,
    HEADERS,
    AddressPropertiesParser,
    HolidayCascadeShift,
)
from waste_collection_schedule.transformers import ICSTransformer

DAYS = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}

# AIS names a property's collection days in fields it does not otherwise mark
# out, so they are found by their value being a weekday code: any "rubbish"
# field is a general-waste round, and the recycling day is named exactly.
_RECYCLE_FIELD = "rubbish_recycle_day"


def _collection_days(properties: dict[str, Any]) -> "tuple[list[int], list[int]]":
    waste_days: list[int] = []
    recycle_days: list[int] = []
    for key, value in properties.items():
        if not isinstance(value, str) or value.upper() not in DAYS:
            continue
        day = DAYS[value.upper()]
        if "rubbish" in key.lower():
            waste_days.append(day)
        if key.lower() == _RECYCLE_FIELD:
            recycle_days.append(day)
    return waste_days, recycle_days


def _describe(properties, source) -> "list[Schedule]":
    """One weekly schedule per round, running to the end of the calendar year."""
    waste_days, recycle_days = _collection_days(properties)
    year = date.today().year
    start, end = date(year, 1, 1), date(year, 12, 31)

    return [
        Schedule(
            key=key,
            start=recurrence.next_weekday(day, on_or_after=start),
            step=recurrence.WEEKLY,
            until=end,
        )
        for key, days in (("general", waste_days), ("recycling", recycle_days))
        for day in days
    ]


@final
class Source(BaseSource):
    TITLE = "City of Philadelphia, PA"
    DESCRIPTION = "City of Philadelphia, PA, USA"
    URL = "https://www.phila.gov/"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"address": "1830 Fitzwater Street"},
        "Test_002": {"address": "9868 Cowden St"},
        "Test_003": {"address": "582 Paoli Ave"},
        "Test_004": {"address": "2714 S Marvine St"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Use your address as shown on the phila.gov trash/recycling "
        "collection-day search results.",
    }

    retrieve = retrievers.LegacyHttpGetRetriever(
        url=lambda address, **_: ADDRESS_URL.format(address=address.upper()),
        headers=HEADERS,
    )
    parse = AddressPropertiesParser()
    preprocess = Compose(
        RecurrenceExpander(_describe),
        HolidayCascadeShift(),
        Deduplicate(),
    )

    transform = ICSTransformer(
        type_value_map={"general": wt.GENERAL_WASTE, "recycling": wt.RECYCLABLES}
    )
