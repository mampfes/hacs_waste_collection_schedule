"""ArmadaleBinCalendar retrieval and parsing through the shared, verified HTTP session."""

import datetime
from typing import Any

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.preprocessors import Schedule
from waste_collection_schedule.retrievers import Request

API_URL = "https://api.my.armadale.wa.gov.au/bins"


class _CalendarClient:
    def __init__(self, address: str):
        self._address: str = address

    def parse(self, r):
        data = r.json()
        if not data:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])
        result = data[0]
        day_name = result["bin_day"]
        bin_day = recurrence.weekday(day_name)
        if bin_day is None:
            raise ValueError(f"Unknown bin day: {day_name}")
        today = datetime.date.today()
        first = recurrence.next_weekday(bin_day, on_or_after=today)
        recycling = result["recycle_area"].lower().startswith("this week")
        if today.weekday() + (first - today).days >= 7:
            recycling = not recycling
        recycling_start = first if recycling else first + recurrence.WEEKLY
        return [
            Schedule("rubbish", first, count=52),
            Schedule(
                "recycling", recycling_start, step=recurrence.FORTNIGHTLY, count=26
            ),
        ]


class CalendarParser(Parser[list[Schedule]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[Schedule]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        return client.parse(response)


calendar_retriever = Request(API_URL, params=lambda address, **_: {"address": address})


def holiday_date(collection_date: datetime.date, _key: str, _source) -> datetime.date:
    """Apply Armadale's existing Christmas/New Year and Good Friday shifts."""
    start_of_week = collection_date - datetime.timedelta(days=collection_date.weekday())
    christmas = datetime.date(collection_date.year, 12, 25)
    new_year = datetime.date(collection_date.year + (collection_date.month == 12), 1, 1)
    shifted = collection_date
    if (
        start_of_week <= christmas <= collection_date
        or start_of_week <= new_year <= collection_date
    ):
        if christmas.weekday() < 5:
            shifted += datetime.timedelta(days=1)
    if shifted == recurrence.good_friday(collection_date.year):
        shifted += datetime.timedelta(days=1)
    return shifted
