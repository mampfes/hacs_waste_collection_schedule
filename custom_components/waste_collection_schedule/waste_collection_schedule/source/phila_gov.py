"""City of Philadelphia, PA.

Composes: :mod:`~waste_collection_schedule.service.PhilaGov` (the city's AIS
address index and its published observed-holiday calendar) with
:class:`~waste_collection_schedule.preprocessors.RecurrenceExpander`. AIS gives
the weekdays a property's rounds are collected on and nothing else, so the year
is projected weekly from them; the city's own holiday feed then slides whatever
lands after a holiday (a secondary trash-only round is cancelled in a holiday
week instead), and two collections pushed onto one day collapse in the
:class:`~waste_collection_schedule.preprocessors.Deduplicate`.
"""

from datetime import date
from typing import ClassVar, final

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

# AIS names a property's collection days in two fields. The primary day is
# trash and recycling; the secondary day (where there is one) is trash only, and
# it is cancelled rather than shifted in a week with a holiday.
_ROUNDS = (
    ("rubbish_recycle_day", ("general", "recycling")),
    ("secondary_rubbish_day", ("secondary",)),
)
_SAME_STREAM = {"secondary": "general"}


def _describe(properties, source) -> "list[Schedule]":
    """One weekly schedule per round, running to the end of the calendar year."""
    year = date.today().year
    start, end = date(year, 1, 1), date(year, 12, 31)

    schedules = []
    for field, keys in _ROUNDS:
        value = properties.get(field)
        if not isinstance(value, str) or value.upper() not in DAYS:
            continue
        first = recurrence.next_weekday(DAYS[value.upper()], on_or_after=start)
        schedules.extend(
            Schedule(key=key, start=first, step=recurrence.WEEKLY, until=end)
            for key in keys
        )
    return schedules


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
        HolidayCascadeShift(cancel_in_holiday_weeks=("secondary",)),
        # The secondary round is general waste too: one per day.
        Deduplicate(key=lambda row: (row[0], _SAME_STREAM.get(row[1], row[1]))),
    )

    transform = ICSTransformer(
        type_value_map={
            "general": wt.GENERAL_WASTE,
            "secondary": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
        }
    )
