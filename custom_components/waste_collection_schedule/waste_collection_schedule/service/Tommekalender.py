"""The "tømmekalender" page Norwegian municipalities publish (Sandnes, Stavanger).

A property's calendar (``.../tommekalender/show?id=...&gnumber=...``) lists one
``tr.waste-calendar__item`` per collection day, the date without a year
("02.10 - fredag") and every fraction collected that day as an icon whose
``title`` names it::

    <tr class="waste-calendar__item">
      <td> 02.10 - fredag </td>
      <td><img title="Plastemballasje"/> <img title="Restavfall"/></td>
    </tr>

:class:`TommekalenderParser` yields one ``(date, fraction)`` row per icon. The
calendar runs a few months ahead from today, so the year is the one that puts
the date nearest today.
"""

import datetime
import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import date_parsers
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_DAY_MONTH = re.compile(r"\d{1,2}\.\d{1,2}")
_parse = date_parsers.nearest_year("%d.%m")


class TommekalenderParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, fraction)`` rows, one per fraction icon."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows: list[tuple[datetime.date, str]] = []
        for item in soup.select("tr.waste-calendar__item"):
            cell = item.select_one("td")
            match = _DAY_MONTH.search(cell.get_text()) if cell is not None else None
            if match is None:
                continue  # the header row
            day = _parse(match.group(0))
            for icon in item.select("img[title]"):
                rows.append((day, str(icon["title"]).strip()))
        return rows
