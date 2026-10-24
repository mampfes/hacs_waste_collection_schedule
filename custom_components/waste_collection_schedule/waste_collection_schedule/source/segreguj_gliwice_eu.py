"""Gliwice, Poland: single-family housing (zabudowa jednorodzinna).

The city's download page links the year's schedule as one spreadsheet
(``Harmonogram_Gliwice_Zabudowa_Jednorodzina_<year>.xlsx``) beside one PDF per
district carrying the same dates. The spreadsheet has a sheet per round, a row
per street (streets split by house number get one row per range, e.g.
"Rolników od nr 237 nieparzyste"), and a column per month headed "sty.26".
Each cell lists that month's collection days: "3 (1), 15, 29", where "3 (1)" is
a holiday shift, collected on the 3rd instead of the 1st.

Two more sheets date the washing of the bio and mixed-waste containers
("Mycie pojemników ..."). A wash is not a collection, so it is typed OTHER and
keeps the sheet's wording as its description.
"""

import datetime
import re
from collections.abc import Iterable, Iterator
from typing import Any, ClassVar, final

from waste_collection_schedule import (
    parsers,
    preprocessors,
    recurrence,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.transformers import ICSTransformer

_FILES_URL = "https://segreguj.gliwice.eu/harmonogram-wywozu-pliki-do-pobrania/"
_XLSX_PATTERN = r"jednorodzin[^/]*?(20\d\d)[^/]*\.xlsx"

# Sheet name -> round label, matched in order (the washing sheets also name
# their container's round). "\bbio": "odbior" (no diacritics) contains "bio".
_SHEETS = (
    (re.compile(r"mycie.*\bbio", re.IGNORECASE), "Mycie pojemników bio"),
    (re.compile(r"mycie.*zmie", re.IGNORECASE), "Mycie pojemników zmieszane"),
    (re.compile(r"mycie", re.IGNORECASE), None),
    (re.compile(r"\bbio", re.IGNORECASE), "Bioodpady"),
    (re.compile(r"tekstyl", re.IGNORECASE), "Tekstylia"),
    (re.compile(r"zmie", re.IGNORECASE), "Odpady zmieszane i segregowane"),
)

# Mixed waste and the segregated bags (paper, plastics and metal, glass) are
# collected together, on one date.
_TYPES = {
    "Odpady zmieszane i segregowane": [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
    ],
    "Bioodpady": wt.ORGANIC,
    "Tekstylia": wt.TEXTILES,
    "Mycie pojemników bio": wt.OTHER,
    "Mycie pojemników zmieszane": wt.OTHER,
}

_MONTH_HEADER = re.compile(r"([^\W\d_]+)\.?\s*(\d{2}|\d{4})")
# A day, optionally followed by the day it was moved from: "3 (1)".
_DAY = re.compile(r"(\d{1,2})(?:\s*\(\d{1,2}\))?")

# The workbook's sheets: three rounds and two container washes. A missing sheet
# fails loudly; which round each one is comes from its name (_SHEETS).
_SHEET_COUNT = 5


def _label(sheet_name: str) -> str | None:
    for pattern, label in _SHEETS:
        if pattern.search(sheet_name):
            return label
    return None


def _workbook(
    response: Any, source: BaseSource | None = None
) -> list[parsers.XlsxSheet]:
    """Every sheet of the workbook, read by the shared XLSX parser."""
    return [
        parsers.XlsxParser(sheet=index, dates=False).read(response, source)
        for index in range(_SHEET_COUNT)
    ]


def _text(cell: Any) -> str:
    return "" if cell is None else str(cell).strip()


def _months(header: list[Any]) -> dict[int, tuple[int, int]]:
    """Column -> (year, month) for the header's "sty.26" cells."""
    columns = {}
    for column, cell in enumerate(header):
        match = _MONTH_HEADER.fullmatch(_text(cell))
        month = (
            recurrence.month(match.group(1), "pl", abbreviated=True) if match else None
        )
        if match and month:
            year = int(match.group(2))
            columns[column] = (year + 2000 if year < 100 else year, month)
    return columns


def _street_dates(
    sheets: list[parsers.XlsxSheet], source: BaseSource | None = None
) -> Iterator[tuple[str, datetime.date, str]]:
    """One workbook's ``(street, date, label)`` rows."""
    read = 0
    for sheet in sheets:
        label = _label(sheet.name)
        if label is None or not sheet.rows:
            continue
        months = _months(sheet.rows[0])
        response_shape.expect(
            bool(months),
            source_name=response_shape.source_name(source),
            detail=f"no month columns in the header of sheet {sheet.name!r}",
            raw=repr(sheet.rows[0]),
        )
        read += 1
        rows: dict[str, list[set[datetime.date]]] = {}
        for row in sheet.rows[1:]:
            name = _text(row[0]) if row else ""
            if not name:
                continue
            dates = set()
            for column, (year, month) in months.items():
                cell = row[column] if column < len(row) else None
                for day in _DAY.findall(_text(cell)):
                    try:
                        dates.add(datetime.date(year, month, int(day)))
                    except ValueError:
                        continue
            rows.setdefault(name, []).append(dates)
        for name, variants in rows.items():
            # A street listed twice (it runs through two districts) keeps only
            # the dates both rows agree on.
            for date in sorted(set.intersection(*variants)):
                yield name, date, label
    response_shape.expect(
        read > 0,
        source_name=response_shape.source_name(source),
        detail="no collection sheet in the workbook",
        raw=repr([sheet.name for sheet in sheets]),
    )


def _streets(
    records: Iterable[tuple[str, datetime.date, str]], source: BaseSource | None
) -> dict[str, list[tuple[datetime.date, str]]]:
    table: dict[str, list[tuple[datetime.date, str]]] = {}
    for name, date, label in records:
        table.setdefault(name, []).append((date, label))
    return table


@final
class Source(BaseSource):
    TITLE = "Gliwice"
    DESCRIPTION = (
        "Source for single-family housing waste collection in Gliwice, Poland."
    )
    URL = "https://segreguj.gliwice.eu"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@maureis"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.ORGANIC,
        wt.TEXTILES,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Agrestowa": {"street": "Agrestowa"},
        "Rolnikow od nr 237 nieparzyste": {"street": "Rolników od nr 237 nieparzyste"},
        "Strzelcow Bytomskich": {"street": "Strzelców Bytomskich"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Rolnikow without house number range": {"street": "Rolników"},
    }

    PARAMS = (street(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street exactly as listed in the single-family housing "
            "schedule (Harmonogram_Gliwice_Zabudowa_Jednorodzina) on "
            "https://segreguj.gliwice.eu/harmonogram-wywozu-pliki-do-pobrania/. "
            "Streets split by house number are listed once per range, e.g. "
            "'Rolników od nr 237 nieparzyste'; enter the whole entry."
        ),
    }

    # Around New Year the page links two years' spreadsheets; read each.
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _FILES_URL, pick=retrievers.yearly_links(_XLSX_PATTERN)
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(_workbook, then=_street_dates)
    preprocess = preprocessors.Compose(
        preprocessors.ArgumentLookup(_streets, argument="street"),
        preprocessors.FlattenGroups(),
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
