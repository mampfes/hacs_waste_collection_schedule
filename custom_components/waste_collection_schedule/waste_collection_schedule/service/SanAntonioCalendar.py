"""San Antonio calendar URLs, parsing and provider holiday shifts."""

from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import quote

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.parsers import Parser

API_URL = "https://gis.sanantonio.gov/swmd/mycollectionday/Request.aspx?addr={addr}"


def calendar_url(address: str) -> str:
    if address is None or not address.strip():
        raise SourceArgumentRequired("address", "Address is required")
    return API_URL.format(addr=quote(address))


def _get_shifting_holidays(year: int) -> list[date]:
    return [
        recurrence.monthly_nth_weekday(3, 4, on_or_after=date(year, 11, 1)),
        date(year, 12, 25),
        date(year, 1, 1),
        recurrence.monthly_nth_weekday(0, 3, on_or_after=date(year, 1, 1)),
    ]


def _get_week_bounds(d: date) -> tuple[date, date]:
    days_since_sunday = (d.weekday() + 1) % 7
    week_start = d - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return (week_start, week_end)


def _adjust_for_holidays(collection_date: date) -> date:
    collection_dow = collection_date.weekday()
    if collection_dow > 4:
        return collection_date
    for year in range(collection_date.year - 1, collection_date.year + 2):
        for holiday in _get_shifting_holidays(year):
            week_start, week_end = _get_week_bounds(holiday)
            if week_start <= collection_date <= week_end:
                if collection_dow >= holiday.weekday():
                    return collection_date + timedelta(days=1)
    return collection_date


def _get_next_day_of_week(day_name: str, *, weeks: int = 4) -> list[date]:
    weekday = recurrence.weekday(day_name)
    if weekday is None:
        return []
    dates = recurrence.recurring(
        recurrence.next_weekday(weekday), recurrence.WEEKLY, weeks
    )
    return [_adjust_for_holidays(d) for d in dates]


def _parse_week_of_date(date_str: str) -> date | None:
    if not date_str or not date_str.startswith("Week of "):
        return None
    date_part = date_str.replace("Week of ", "").strip()
    return datetime.strptime(date_part, "%m/%d/%Y").date()


class _CalendarClient:
    def __init__(self, address: str):
        if address is None or address.strip() == "":
            raise SourceArgumentRequired("address", "Address is required")
        self._address: str = address

    def parse(self, r):
        data = r.json()
        if data == []:
            raise ValueError("Address not found")
        entries: list[dict] = []
        if not data:
            return entries
        attributes = data[0].get("attributes", {})
        no_service = True
        for waste_type in ("Garbage", "Recycle", "Organics"):
            day_name = attributes.get(waste_type)
            no_svc = day_name == "NO SERVICE"
            no_service &= no_svc
            if not day_name or no_svc:
                continue
            if waste_type == "Organics" and (not attributes.get("isQualifyOrganics")):
                continue
            for collection_date in _get_next_day_of_week(day_name):
                entries.append({"date": collection_date, "type": waste_type})
        for waste_type in ("Brush", "Bulky"):
            date_str = attributes.get(waste_type)
            parsed_date = _parse_week_of_date(date_str)
            if parsed_date:
                entries.append({"date": parsed_date, "type": waste_type})
        if no_service and (not entries):
            raise ValueError(f"No waste collection service found for {self._address}")
        return entries


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        response.raise_for_status()
        return client.parse(response)
