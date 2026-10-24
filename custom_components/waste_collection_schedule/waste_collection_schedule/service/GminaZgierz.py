"""The yearly waste schedule article of Gmina Zgierz (``bip.gminazgierz.pl``).

The BIP article API answers with JSON whose ``content`` is the HTML of the
schedule and whose ``title`` names the year ("... na 2026 rok"). The article
holds, per collection region ("Rejon I" to "Rejon IV"):

* a table with a row per month and a column per round (segregated and residual
  waste, BIO), each cell listing the days of that month, sometimes with a
  note in brackets about a holiday move ("3 (za 4 czerwca)": collected on the
  3rd instead of the 4th);
* a "Gabaryty" row with the dated bulky-waste collections ("16 maja, 5 września");
* a paragraph per region listing the villages that belong to it.

:class:`ZgierzParser` yields ``(date, label)`` rows for the region of the
configured village.
"""

import datetime
import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule import recurrence
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_REGION_PARAGRAPH = re.compile(r"^(Rejon [IV]+)\s*:\s*(.*)$", re.DOTALL)
_BRACKETS = re.compile(r"\([^)]*\)")
_DAY_MONTH = re.compile(r"(\d{1,2})\s+([^\W\d_]+)")


def _norm(text: str) -> str:
    return " ".join(_BRACKETS.sub("", text).split()).casefold()


def _regions(soup: BeautifulSoup) -> dict[str, list[str]]:
    """The villages of every region, as listed in the article's paragraphs."""
    regions: dict[str, list[str]] = {}
    for paragraph in soup.find_all("p"):
        match = _REGION_PARAGRAPH.match(" ".join(paragraph.get_text().split()))
        if match is None:
            continue
        villages = [v.strip(" .") for v in match.group(2).split(",")]
        regions[match.group(1)] = [v for v in villages if v]
    return regions


class ZgierzParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, round name)`` rows for the village in ``location_name``."""

    def __init__(self, argument: str = "location_name"):
        self.argument = argument

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        data = response.json()
        soup = BeautifulSoup(data.get("content") or "", "html.parser")
        location = str(source.params[self.argument] if source else "")

        regions = _regions(soup)
        region = next(
            (
                name
                for name, villages in regions.items()
                if _norm(location) in {_norm(v) for v in villages}
            ),
            None,
        )
        if region is None:
            raise SourceArgumentNotFoundWithSuggestions(
                self.argument,
                location,
                sorted({v for villages in regions.values() for v in villages}),
            )

        found = re.search(r"\b(20\d{2})\b", str(data.get("title", "")))
        year = int(found.group(1)) if found else datetime.date.today().year

        # The article's own typo "Rejon I I" for "Rejon II".
        pattern = re.compile(r"\b" + re.escape(region) + r"\b")
        table = None
        for candidate in soup.find_all("table"):
            first = candidate.find("tr")
            if first is not None and pattern.search(
                first.get_text(" ").replace("Rejon I I", "Rejon II")
            ):
                table = candidate
                break
        if table is None:
            return []

        header = [
            " ".join(cell.get_text(" ").split()).replace("Rejon I I", "Rejon II")
            for cell in table.find("tr").find_all("td")  # type: ignore[union-attr]
        ]
        rounds = {
            index: ("BIO" if "BIO" in text else "Segregowane i zmieszane")
            for index, text in enumerate(header)
            if pattern.match(text)
        }
        # Bulky waste is one cell per pair of regions: Rejon I/III, then II/IV.
        bulky_cell = 1 if (recurrence.roman(region.split()[1]) or 0) % 2 else 2

        rows: list[tuple[datetime.date, str]] = []
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            title = cells[0].get_text(strip=True)
            month = recurrence.month(title)
            if month is not None:
                for index, name in rounds.items():
                    if index >= len(cells):
                        continue
                    text = _BRACKETS.sub("", cells[index].get_text(" "))
                    for day in re.findall(r"\d+", text):
                        try:
                            rows.append((datetime.date(year, month, int(day)), name))
                        except ValueError:
                            continue
            elif "gabaryty" in title.casefold() and bulky_cell < len(cells):
                cell: Tag = cells[bulky_cell]
                for day, month_name in _DAY_MONTH.findall(cell.get_text(" ")):
                    bulky_month = recurrence.month(month_name)
                    if bulky_month is None:
                        continue
                    try:
                        rows.append(
                            (datetime.date(year, bulky_month, int(day)), "Gabaryty")
                        )
                    except ValueError:
                        continue
        return rows
