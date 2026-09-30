import datetime
from functools import lru_cache
from typing import Any, ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import (
    ArgumentLookup,
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

BASE_URL = "https://devcorrpublicdatahub.blob.core.usgovcloudapi.net/garbage-recycling"
ZONES_URL = f"{BASE_URL}/garbagerecyclingzones.json"
DAYS_URL = f"{BASE_URL}/garbagerecyclingdays.json"

RECYCLING = "Recycling"
TRASH = "Trash"

# Collections falling on these days are moved back by one day (per the city).
_SHIFTED_HOLIDAYS = ("Thanksgiving", "Christmas", "New Year")


def _neighborhoods(records: list[dict[str, Any]], source) -> dict[str, Any]:
    """Both JSON files (concatenated) -> ``{neighborhood: (zone, recycling dates)}``."""
    zone_dates: dict[str, list[datetime.date]] = {}
    for record in records:
        if "Date" in record:
            zone_dates.setdefault(record["Recycling Zone"], []).append(
                datetime.date.fromisoformat(record["Date"])
            )
    return {
        record["Neighborhood Name"]: (
            record["Recycling Zone"],
            zone_dates.get(record["Recycling Zone"], []),
        )
        for record in records
        if "Neighborhood Name" in record
    }


def _describe(record, source):
    """Recycling on the published dates; weekly trash on the zone's weekday."""
    zone, dates = record
    for collection_date in dates:
        yield Schedule(RECYCLING, collection_date)
    weekday = recurrence.weekday(zone.split(" ")[0])
    if weekday is not None and dates:
        yield Schedule(TRASH, recurrence.next_weekday(weekday), until=max(dates))


@lru_cache(maxsize=8)
def _holidays(year: int) -> dict[datetime.date, str]:
    return recurrence.us_federal_holidays(year, observed=False)


def _adjust(collection_date: datetime.date, key: str, source) -> datetime.date:
    name = _holidays(collection_date.year).get(collection_date, "")
    if any(holiday in name for holiday in _SHIFTED_HOLIDAYS):
        return collection_date + datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "Round Rock Texas"
    DESCRIPTION = "Source for bin collection services for Round Rock, Texas"
    URL = "https://www.roundrocktexas.gov/"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Apache Oaks": {"neighborhood": "Apache Oaks"},
        "Mayfield Ranch": {"neighborhood": "Mayfield Ranch"},
        "Windy Park": {"neighborhood": "Windy Park"},
    }

    PARAMS = (text_field("neighborhood", "Neighborhood"),)

    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the name of your neighborhood as the City of Round Rock "
            "lists it (for example Apache Oaks or Windy Park). Recycling is "
            "collected every two weeks and trash weekly, on the weekday of "
            "your neighborhood's recycling zone."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        targets=lambda source, context: (ZONES_URL, DAYS_URL)
    )
    parse = parsers.EachResponse(parsers.JsonParser())
    preprocess = Compose(
        ArgumentLookup(_neighborhoods, argument="neighborhood"),
        RecurrenceExpander(_describe),
        HolidayShift(_adjust),
    )
    transform = ICSTransformer(
        type_value_map={TRASH: wt.GENERAL_WASTE, RECYCLING: wt.RECYCLABLES}
    )
