"""AksdCalendar retrieval and parsing, using the pipeline HTTP session."""

import json
import re
import unicodedata
from datetime import date, timedelta
from typing import Any

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.preprocessors import Schedule
from waste_collection_schedule.retrievers import RetrieverFunc

NAME_MAP = {
    "black": "General waste",
    "yellow": "Recycling",
    "brown": "Garden waste (bin)",
    "green": "Garden waste (bag)",
    "lockable": "Food waste",
}
SEASONAL_TYPES = {"brown", "green"}
SEASON_MONTHS = range(3, 13)
ZIP_CODE = "4024"
CALENDAR_URL = "https://www.aksd.hu/hulladeknaptar"
ZIP_URL = "https://www.aksd.hu/ajax/save_customer_zip"
DAYS_AHEAD = 366


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in text if not unicodedata.combining(c))


def _parse_rule(text: str) -> tuple[bool, set[int]]:
    """Return (odd_weeks_only, weekdays) for a text such as
    "Csütörtök" or "Minden páratlan héten kedd vagy péntek"."""
    norm = _normalize(text)
    odd_only = "paratlan" in norm
    days = {
        day
        for word in re.findall("[a-z]+", norm)
        if (day := recurrence.weekday(word)) is not None
    }
    return (odd_only, days)


class _CalendarClient:
    _session: Any

    def __init__(self, street: str):
        self._street = street

    def _get_streets(self) -> list[dict]:
        session = self._session
        r = session.get(CALENDAR_URL, timeout=30)
        r.raise_for_status()
        r = session.post(
            ZIP_URL,
            data={"zip": ZIP_CODE, "type": "residential", "close": "false"},
            timeout=30,
        )
        r.raise_for_status()
        r = session.get(CALENDAR_URL, timeout=30)
        r.raise_for_status()
        return r

    def retrieve(self):
        return self._get_streets()

    def parse(self, response):
        match = re.search(
            "const wasteCalendarStreets = (\\[.*?\\]);\\s*\\n", response.text
        )
        if not match:
            raise ValueError("Could not find street data on the AKSD calendar page")
        streets = json.loads(match.group(1))
        wanted = _normalize(self._street)
        street = next(
            (
                s
                for s in streets
                if wanted == _normalize(s["label"])
                or wanted in [_normalize(v) for v in s.get("searchValues", [])]
            ),
            None,
        )
        if street is None:
            suggestions = sorted(
                {
                    s["label"]
                    for s in streets
                    if wanted and wanted in _normalize(s["label"])
                }
            )
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street", self._street, suggestions[:20]
                )
            raise SourceArgumentNotFound("street", self._street)
        today = date.today()
        schedules = []
        for bin_type, rules in street["options"].items():
            for rule in rules:
                odd_only, weekdays = _parse_rule(rule)
                for weekday in sorted(weekdays):
                    schedules.append(
                        Schedule(
                            key=NAME_MAP.get(bin_type) or str(bin_type),
                            start=recurrence.next_weekday(weekday, on_or_after=today),
                            until=today + timedelta(days=DAYS_AHEAD - 1),
                            iso_week_parity="odd" if odd_only else None,
                        )
                    )
        return schedules


def in_season(row, _source) -> bool:
    collection_date, label = row
    return (
        label not in {NAME_MAP[t] for t in SEASONAL_TYPES}
        or collection_date.month in SEASON_MONTHS
    )


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[Schedule]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[Schedule]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
