"""PalmCoastCalendar retrieval and parsing through the shared, verified HTTP session."""

from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request

from ..exceptions import SourceArgumentNotFound

API_URL = "https://www.palmcoast.gov/SalesforceDynamicForm/Schedule"


class _CalendarClient:
    def __init__(self, street: str):
        self._street = street.strip()

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
        return [schedule_data[0]]


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        return client.parse(response)


calendar_retriever = Request(
    API_URL, params=lambda street, **_: {"address": street.strip()}, timeout=30
)
