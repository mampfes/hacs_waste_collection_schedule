"""ArmadaleBinCalendar retrieval and parsing through the shared, verified HTTP session."""

import datetime
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}
API_URL = "https://api.my.armadale.wa.gov.au/bins"


def easter(year):
    y = year
    g = y % 19
    e = 0
    c = y // 100
    h = (c - c // 4 - (8 * c + 13) // 25 + 19 * g + 15) % 30
    i = h - h // 28 * (1 - h // 28 * (29 // (h + 1)) * ((21 - g) // 11))
    j = (y + y // 4 + i + 2 - c + c // 4) % 7
    p = i - j + e
    d = 1 + (p + 27 + (p + 6) // 40) % 31
    m = 3 + (p + 26) // 30
    return datetime.date(int(y), int(m), int(d))


class _CalendarClient:
    _session: Any

    def __init__(self, address: str):
        self._address: str = address

    def retrieve(self):
        r = self._session.get(API_URL, params={"address": self._address})
        r.raise_for_status()
        return r

    def parse(self, r):
        data = r.json()
        if not data:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])
        result = data[0]
        bin_day = result["bin_day"]
        if bin_day not in WEEKDAYS:
            raise ValueError(f"Unknown bin day: {bin_day}")
        bin_day = WEEKDAYS[bin_day]
        recycling: bool = result["recycle_area"].lower().startswith("this week")
        current_day = datetime.datetime.now().date()
        diff_to_next = (bin_day - current_day.weekday()) % 7
        if current_day.weekday() + diff_to_next >= 7:
            recycling = not recycling
        current_day = current_day + datetime.timedelta(days=diff_to_next)
        entries = []
        for _i in range(52):
            date = current_day
            start_of_week = date - datetime.timedelta(days=date.weekday())
            christmas = datetime.date(current_day.year, 12, 25)
            new_years_day = datetime.date(
                current_day.year + (1 if current_day.month == 12 else 0), 1, 1
            )
            good_friday = easter(current_day.year) - datetime.timedelta(days=2)
            if (
                start_of_week <= christmas <= date
                or start_of_week <= new_years_day <= date
            ):
                if 0 <= christmas.weekday() < 5:
                    date += datetime.timedelta(days=1)
            if date == good_friday:
                date += datetime.timedelta(days=1)
            entries.append({"date": date, "type": "rubbish"})
            if recycling:
                entries.append({"date": date, "type": "recycling"})
            current_day += datetime.timedelta(days=7)
            recycling = not recycling
        return entries


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
