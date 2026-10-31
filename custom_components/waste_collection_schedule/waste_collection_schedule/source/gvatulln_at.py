"""GVA Tulln (gvatulln.at), Lower Austria.

The Gemeindeverband für Abfallwirtschaft im Raum Tulln publishes one Excel
collection plan per member municipality (26 of them) on its "Abholtermine" page,
next to the PDF of the same plan. The XLSX links are found by their link text
("Abfuhrplan Tulln 2026 EXCEL") with ``retrievers.yearly_links``, so next year's
plan is read as well once it is posted while this year's is still running.

Each workbook has one sheet in the same shape: row 2 names one column per
collection round ("Restmüll", "Altpapier Sprengel 1 + 3", "Gelbe Tonne") and the
dates run down below it, read with the shared ``parsers.XlsxParser``. The
columns form two blocks separated by an empty column: households on the left,
"Gewerbe und Wohnhausanlagen" (businesses and apartment complexes, with yellow
bins instead of yellow bags) on the right. A municipality split into collection
districts names them in the header, as "Sprengel" numbers (several per column
when they share a round) or, in Zeiselmauer-Wolfpassing, as the village name.

A handful of cells hold text instead of a date: two-day rounds ("Mo, 13.04./Di,
14.04.") yield their first day, and remarks ("Mi markieren") are skipped.
"""

import datetime
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import lookups, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, dropdown, municipality
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

INDEX_URL = "https://gvatulln.at/fuer-die-bevoelkerung/abholtermine/"

# The Excel plans, by file name: "Abfuhrplan-Tulln-2026-EXCEL.xlsx",
# "Abfuhrplan-Zwentendorf-2026-FERTIG.xlsx".
_XLSX_PATTERN = r"Abfuhrplan-[^/]*?(20\d\d)[^/]*\.xlsx$"

_HOUSEHOLD = "household"
_COMMERCIAL = "commercial"

# A column header: the bin, then optionally the districts it is for.
_HEADER = re.compile(
    r"^(Restmüll|Altpapier|Biomüll|Bio|Gelber\s+Sack|Gelbe\s+Tonne)\b\s*(.*)$",
    re.IGNORECASE,
)
_SPRENGEL = re.compile(r"^Sprengel\s+(.*)$", re.IGNORECASE)
_DAY_MONTH = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.")


def _municipality_name(link_text: str) -> str:
    """ "Abfuhrplan St. Andrä-Wördern 2026 EXCEL" -> "St. Andrä-Wördern"."""
    return re.sub(r"^\s*Abfuhrplan\s+|\s+20\d\d\b.*$", "", link_text)


def _blocks(header: list[Any]) -> list[list[int]]:
    """Column indexes of each run of headed columns, left to right."""
    blocks: list[list[int]] = []
    previous = -2
    for index, title in enumerate(header):
        if not isinstance(title, str) or not title.strip():
            continue
        if index != previous + 1 or not blocks:
            blocks.append([])
        blocks[-1].append(index)
        previous = index
    return blocks


def _split_header(title: str) -> tuple[str, str | None, list[str]]:
    """Bin label, district text and district keys of one column header.

    "Altpapier Sprengel 2+4+5" -> ("Altpapier", "Sprengel 2+4+5", ["2", "4", "5"]);
    "Altpapier Wolfpassing" -> ("Altpapier", "Wolfpassing", ["wolfpassing"]);
    "Restmüll" -> ("Restmüll", None, []).
    """
    title = " ".join(title.split())
    match = _HEADER.match(title)
    if not match:
        return title, None, []
    label, rest = " ".join(match.group(1).split()), match.group(2).strip()
    if not rest:
        return label, None, []
    sprengel = _SPRENGEL.match(rest)
    if sprengel:
        return label, rest, re.findall(r"\d+", sprengel.group(1))
    return label, rest, [lookups.normalize_loose(rest)]


def _date(value: Any, year: int) -> datetime.date | None:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        match = _DAY_MONTH.search(value)
        if match:
            return datetime.date(year, int(match.group(2)), int(match.group(1)))
    return None


def _plan_year(grid: list[list[Any]]) -> int:
    """The year most of the plan's dates fall in (for the text-only cells)."""
    years = [
        cell.year for row in grid for cell in row if isinstance(cell, datetime.date)
    ]
    return max(set(years), key=years.count) if years else datetime.date.today().year


def _rows(
    grid: list[list[Any]], source: BaseSource | None = None
) -> list[tuple[datetime.date, str]]:
    """The (date, bin) pairs of one plan for the configured district and building."""
    params = source.params if source is not None else {}
    building = params.get("building") or _HOUSEHOLD
    wanted = params.get("district")
    blocks = _blocks(grid[1]) if len(grid) > 2 else []
    if not blocks or (building != _HOUSEHOLD and len(blocks) < 2):
        return []
    block = blocks[0] if building == _HOUSEHOLD else blocks[-1]
    columns = [(index, *_split_header(str(grid[1][index]))) for index in block]
    offered = sorted(
        {text for _, _, text, _ in columns if text},
        key=lambda text: (not text.lower().startswith("sprengel"), text),
    )
    if offered and not wanted:
        raise SourceArgumentRequiredWithSuggestions(
            "district",
            "this municipality's plan is split into collection districts",
            offered,
        )
    key = lookups.normalize_loose(wanted) if wanted else None
    if key and key.startswith("sprengel "):
        key = key.removeprefix("sprengel ").strip()
    selected = [
        (index, label)
        for index, label, text, keys in columns
        if text is None or key in keys
    ]
    if offered and not any(key in keys for _, _, _, keys in columns):
        raise SourceArgumentNotFoundWithSuggestions("district", wanted, offered)
    year = _plan_year(grid)
    entries: list[tuple[datetime.date, str]] = []
    for row in grid[2:]:
        for index, label in selected:
            day = _date(row[index], year)
            if day is not None:
                entries.append((day, label))
    return entries


@final
class Source(BaseSource):
    TITLE = "GVA Tulln"
    DESCRIPTION = (
        "Source for the Gemeindeverband für Abfallwirtschaft im Raum Tulln (AT)."
    )
    URL = "https://gvatulln.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Großweikersdorf": {"municipality": "Großweikersdorf"},
        "Tulln Sprengel 2": {"municipality": "Tulln", "district": "2"},
        "Zeiselmauer-Wolfpassing, Wolfpassing": {
            "municipality": "Zeiselmauer-Wolfpassing",
            "district": "Wolfpassing",
        },
        "Pressbaum Sprengel 3, commercial": {
            "municipality": "Pressbaum",
            "district": "Sprengel 3",
            "building": "commercial",
        },
    }

    PARAMS = (
        municipality(),
        district(optional=True),
        dropdown(
            "building",
            [_HOUSEHOLD, _COMMERCIAL],
            label="Building type",
            default=_HOUSEHOLD,
        ),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality as it is named on "
            "https://gvatulln.at/fuer-die-bevoelkerung/abholtermine/ (e.g. "
            "'Tulln', 'St. Andrä-Wördern', 'Sitzenberg'). Municipalities split "
            "into collection districts also need the district: the 'Sprengel' "
            "number from the plan (e.g. '2'), or 'Zeiselmauer' / 'Wolfpassing'. "
            "Choose building type 'commercial' for businesses and apartment "
            "complexes (Gewerbe und Wohnhausanlagen)."
        ),
        "de": (
            "Geben Sie Ihre Gemeinde so ein, wie sie auf "
            "https://gvatulln.at/fuer-die-bevoelkerung/abholtermine/ heißt (z. B. "
            "'Tulln', 'St. Andrä-Wördern', 'Sitzenberg'). Gemeinden mit mehreren "
            "Sprengeln brauchen zusätzlich den Sprengel: die Nummer aus dem "
            "Abfuhrplan (z. B. '2') bzw. 'Zeiselmauer' / 'Wolfpassing'. "
            "Gebäudetyp 'commercial' gilt für Gewerbe und Wohnhausanlagen."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            INDEX_URL,
            pick=retrievers.yearly_links(
                _XLSX_PATTERN,
                argument="municipality",
                link_name=_municipality_name,
            ),
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(parsers.XlsxParser(), then=_rows)
    transform = ICSTransformer(
        type_value_map={
            "Gelber Sack": wt.RECYCLABLES,
            "Gelbe Tonne": wt.RECYCLABLES,
        },
    )
