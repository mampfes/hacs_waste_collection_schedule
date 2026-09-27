"""The "tømmekalender" page Norwegian municipalities publish (Sandnes, Stavanger).

A property's calendar (``.../tommekalender/show?id=...&gnumber=...``) lists one
``tr.waste-calendar__item`` per collection day, the date without a year
("02.10 - fredag") and every fraction collected that day as an icon whose
``title`` names it. Each row's enclosing ``tbody[data-month]`` provides the
calendar month and year (for example, ``10-2026``).

:class:`TommekalenderParser` yields one ``(date, fraction)`` row per icon.
"""

import datetime
import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_DAY_MONTH = re.compile(r"\d{1,2}\.\d{1,2}")


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
            month_group = item.find_parent("tbody", attrs={"data-month": True})
            if month_group is None:
                raise ValueError("Collection row has no data-month metadata")
            month, year = (int(part) for part in month_group["data-month"].split("-"))
            day = datetime.datetime.strptime(
                f"{match.group(0)}.{year}", "%d.%m.%Y"
            ).date()
            if day.month != month:
                raise ValueError("Collection date does not match data-month metadata")
            for icon in item.select("img[title]"):
                rows.append((day, str(icon["title"]).strip()))
        return rows
