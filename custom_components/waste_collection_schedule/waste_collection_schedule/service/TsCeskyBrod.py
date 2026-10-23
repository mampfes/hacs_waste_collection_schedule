"""Pipeline components for Technické služby Český Brod (CZ).

The page ``/pravidelny-svoz-odpadu`` publishes no dates, only rules:

* an "odd week" table (residual waste) and an "even week" table (organic waste)
  with one row per weekday listing the streets served that day;
* a note that organic waste is collected every week from April to November, in
  even weeks in March and in the first even week of the month from December to
  February (the page says so in prose, so the cadence lives here);
* the city-wide rounds of paper (Wednesday, odd weeks) and plastic (Thursday,
  even weeks) for household bins.

:class:`TsCeskyBrodParser` reads the street lists from the live page and
:class:`TsCeskyBrodExpander` turns the configured street's weekdays and these
cadences into ``(date, label)`` rows for an ``ICSTransformer``.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import date, timedelta
from typing import TYPE_CHECKING, NamedTuple

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

if TYPE_CHECKING:
    from requests import Response

    from waste_collection_schedule.base_source import BaseSource

RESIDUAL = "Zbytkový komunální odpad"
ORGANIC = "Biologický odpad"
PAPER = "Papír a lepenka"
PLASTIC = "Plasty"

_WEEKDAYS = {
    "pondeli": calendar.MONDAY,
    "utery": calendar.TUESDAY,
    "streda": calendar.WEDNESDAY,
    "ctvrtek": calendar.THURSDAY,
    "patek": calendar.FRIDAY,
}


def normalize(text: str) -> str:
    """Lower-case, collapse whitespace and strip diacritics."""
    text = unicodedata.normalize("NFKD", text.replace("\xa0", " "))
    stripped = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(stripped.lower().split())


class StreetRow(NamedTuple):
    """One table row: the waste it carries, its weekday and its streets."""

    label: str
    weekday: int
    streets: tuple[str, ...]


def split_streets(cell_html_text: str) -> tuple[str, ...]:
    """Split a street cell (``<br>`` already turned into commas) into names."""
    text = cell_html_text.replace("\xa0", " ")
    text = re.sub(r"^\s*Český Brod\s*[–-]\s*", "", text)
    return tuple(" ".join(p.split()) for p in text.split(",") if p.strip())


class TsCeskyBrodParser:
    """Read the odd/even week street tables from the schedule page."""

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[StreetRow]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.text, "html.parser")
        rows: list[StreetRow] = []
        label = ""
        for tr in soup.select("article table tr"):
            head = tr.find_all("th")
            cells = tr.find_all("td")
            if head and not cells:
                title = normalize(head[0].get_text())
                if title.startswith("lichy"):
                    label = RESIDUAL
                elif title.startswith("sudy"):
                    label = ORGANIC
                continue
            if not label or not head or len(cells) < 2:
                continue
            weekday = _WEEKDAYS.get(normalize(head[0].get_text()))
            for br in cells[1].find_all("br"):
                br.replace_with(",")
            streets = split_streets(cells[1].get_text())
            if weekday is not None and streets:
                rows.append(StreetRow(label, weekday, streets))
        response_shape.expect(
            {RESIDUAL, ORGANIC} <= {r.label for r in rows},
            source_name=response_shape.source_name(source),
            detail="no odd/even week street tables found (changed layout?)",
            raw=response.text[:500],
        )
        return rows


def _weekday_of(rows: list[StreetRow], label: str, street: str) -> int | None:
    target = normalize(street)
    for row in rows:
        if row.label == label and any(normalize(s) == target for s in row.streets):
            return row.weekday
    return None


def _organic_collected(day: date) -> bool:
    week = day.isocalendar()[1]
    even = week % 2 == 0
    return (4 <= day.month <= 11) or (even and (day.month == 3 or day.day <= 14))


class TsCeskyBrodExpander:
    """Project the street's weekdays and the city-wide rounds onto dates."""

    def __call__(
        self, rows: list[StreetRow], source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        street = (source.params.get("street") if source is not None else "") or ""
        residual_day = _weekday_of(rows, RESIDUAL, street)
        organic_day = _weekday_of(rows, ORGANIC, street)
        if residual_day is None and organic_day is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                street,
                sorted({s for r in rows for s in r.streets}),
            )

        today = date.today()
        day = date(today.year, 1, 1)
        end = date(today.year + 1, 12, 31)
        result: list[tuple[date, str]] = []
        while day <= end:
            odd = day.isocalendar()[1] % 2 == 1
            weekday = day.weekday()
            if odd and weekday == residual_day:
                result.append((day, RESIDUAL))
            if weekday == organic_day and _organic_collected(day):
                result.append((day, ORGANIC))
            if odd and weekday == calendar.WEDNESDAY:
                result.append((day, PAPER))
            if not odd and weekday == calendar.THURSDAY:
                result.append((day, PLASTIC))
            day += timedelta(days=1)
        return result
