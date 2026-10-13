"""PalmCoastCalendar retrieval and parsing through the shared, verified HTTP session."""

from datetime import datetime, timedelta
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

from ..exceptions import SourceArgumentNotFound

API_URL = "https://www.palmcoast.gov/SalesforceDynamicForm/Schedule"
WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


class _CalendarClient:
    _session: Any

    def __init__(self, street: str):
        self._street = street.strip()

    def retrieve(self):
        session = self._session
        response = session.get(API_URL, params={"address": self._street}, timeout=30)
        response.raise_for_status()
        return response

    def parse(self, response):
        data = response.json()
        if not data.get("success"):
            message = data.get("message", "Unknown error")
            raise SourceArgumentNotFound("street", self._street, message)
        schedule_data = data.get("data", [])
        if not schedule_data:
            raise SourceArgumentNotFound(
                "street", self._street, "No schedule data found"
            )
        schedule = schedule_data[0]
        entries: list[dict] = []
        solid_waste_days = schedule.get("solidWasteDays", "")
        if solid_waste_days:
            entries.extend(self._parse_days(solid_waste_days, "Garbage"))
        yard_waste_days = schedule.get("yardWasteDays", "")
        if yard_waste_days:
            entries.extend(self._parse_days(yard_waste_days, "Yard Waste"))
        recycle_days = schedule.get("recycleDays", "")
        if recycle_days:
            entries.extend(self._parse_days(recycle_days, "Recycling"))
        return entries

    def _parse_days(self, day_string: str, waste_type: str) -> list[dict]:
        """Parse day string like 'Tuesday/Friday' and return Collection entries."""
        days = [day.strip() for day in day_string.split("/") if day.strip()]
        entries = []
        for day in days:
            if day in WEEKDAYS:
                entries.extend(self._weekly_dates(day, waste_type))
        return entries

    def _weekly_dates(self, day_name, waste_type):
        """Generate weekly collection dates for the given day and waste type."""
        weekday_idx = WEEKDAYS.get(day_name)
        if weekday_idx is None:
            return []
        today = datetime.now().date()
        days_ahead = (weekday_idx - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)
        return [
            {"date": next_date + timedelta(weeks=i), "type": waste_type}
            for i in range(26)
        ]


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
