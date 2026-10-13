"""garbage.datenplattform.heidelberg.de: the City of Heidelberg's waste API.

``/collections?street=<name>`` answers a street with its collection *rules*, not
dates: per waste type a weekday (``day_of_week_<type>``, "Mo".."So") and a
week rhythm (``calendar_week_<type>``: ``A`` every week, ``G`` even ISO weeks,
``U`` odd ISO weeks), the street's Christmas tree collection date, and the
city-wide ``exceptions`` list of holiday shifts (a collection on
``shift_from_date`` takes place on ``shift_to_date``).

:class:`ScheduleExpander` projects these rules into ``(date, type)`` rows for an
``ICSTransformer``. Streets that cannot be collected weekly may choose a
fortnightly residual waste round (``weekly_residual=False``), whose week
parity depends on the parity of the house number (``even_house_number``).
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Literal

from babel.dates import get_day_names

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.preprocessors import (
    Preprocessor,
    RecurrenceExpander,
    Schedule,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from waste_collection_schedule.base_source import BaseSource

STREETS_URL = "https://garbage.datenplattform.heidelberg.de/streetnames"
COLLECTIONS_URL = "https://garbage.datenplattform.heidelberg.de/collections"

WEEKLY_TYPES = ("bio", "dsd", "paper", "rest")
CHRISTMAS = "christmas"

_PARITY: dict[str, Literal["even", "odd"]] = {"G": "even", "U": "odd"}

_parse_date = date_parsers.auto

# The API abbreviates weekdays the German way ("Mo", "Di", ...), which the
# shared multilingual weekday lookup deliberately does not register.
_WEEKDAY_ABBREVIATIONS = {
    name.rstrip(".").lower(): number
    for number, name in get_day_names("abbreviated", locale="de").items()
}


def _weekday(name: str) -> int | None:
    return _WEEKDAY_ABBREVIATIONS.get(name.strip().lower(), recurrence.weekday(name))


def street_names(response: Any, **_: Any) -> list[str]:
    """The street names of the ``/streetnames`` reply (``[[name, flag], ...]``)."""
    return [entry[0] for entry in response.json()]


def has_collections(response: Any, source: BaseSource | None = None) -> bool:
    """True when the street resolved (an unknown street answers no collections)."""
    return bool(response.json().get("collections"))


class ScheduleExpander(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """The street's rules and holiday shifts as ``(date, type)`` rows.

    Weekly rounds run from last week to mid-January of next year, matching the
    horizon the city publishes holiday shifts for. Christmas tree collection is
    a single dated entry and is not shifted.
    """

    def __init__(
        self,
        *,
        weekly_residual: str = "collect_residual_waste_weekly",
        even_house_number: str = "even_house_number",
    ):
        self._weekly_residual = weekly_residual
        self._even_house_number = even_house_number
        self._expander = RecurrenceExpander(self._describe)

    def _describe(
        self, record: Mapping[str, Any], source: BaseSource | None
    ) -> Iterable[Schedule]:
        params = source.params if source is not None else {}
        today = datetime.date.today()
        window_start = today - datetime.timedelta(days=7)
        window_end = datetime.date(today.year + 1, 1, 15)
        for waste in WEEKLY_TYPES:
            day = _weekday(record.get(f"day_of_week_{waste}") or "")
            if day is None:
                continue
            rhythm = record.get(f"calendar_week_{waste}")
            if waste == "rest" and params.get(self._weekly_residual) is False:
                rhythm = "G" if params.get(self._even_house_number) else "U"
            yield Schedule(
                key=waste,
                start=recurrence.next_weekday(day, on_or_after=window_start),
                step=recurrence.WEEKLY,
                not_before=window_start,
                until=window_end,
                iso_week_parity=_PARITY.get(rhythm or ""),
            )

    def __call__(
        self, records: Any, source: BaseSource | None = None
    ) -> Iterable[tuple[datetime.date, str]]:
        if isinstance(records, dict):
            records = [records]
        for record in records:
            collections = record.get("collections") or []
            if not collections:
                continue
            shifts = {
                _parse_date(e["shift_from_date"]): _parse_date(e["shift_to_date"])
                for e in record.get("exceptions") or []
            }
            for date, key in self._expander([collections[0]], source):
                yield shifts.get(date, date), key
            for tree in (record.get("christmas") or [])[:1]:
                yield _parse_date(tree["collection_date"]), CHRISTMAS
