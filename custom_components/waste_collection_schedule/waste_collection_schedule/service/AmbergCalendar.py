"""AmbergCalendar calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

import re
from datetime import date, timedelta
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.parsers import Parser, XlsxParser
from waste_collection_schedule.retrievers import RetrieverFunc

VALID_ZONES = [
    f"{letter}{num}"
    for letter in ("A", "B", "C", "D", "E")
    for num in ("1", "2", "3", "4")
]
WASTE_COLUMNS = {
    5: "Rest- und Biomüll",
    7: "Papiertonne",
    8: "Gelber Sack",
    9: "Problemmüll",
    10: "Häckselgut",
    11: "Sperrmüll",
}
_EXCEL_EPOCH = date(1899, 12, 30)
# Columns A..N of the Dateneingabe sheet (date, ..., zone letter, waste columns).
_MAX_COLS = 14
_ABFALL_PAGE = "https://amberg.de/abfallberatung/"
_STREET_DIR_URL = "https://amberg.de/fileadmin/Abfallberatung/Abfuhrkalender/{year}/ICS/{year}_Strassenverzeichnis.json"
_XLSX_URL = "https://amberg.de/fileadmin/Abfallberatung/Abfuhrkalender/{year}/ICS/Abfuhrkalender_{year}_Online{zone}.xlsx"


def _discover_year(session) -> str:
    """Discover the current Abfuhrkalender year from the Abfallberatung overview page."""
    response = session.get(_ABFALL_PAGE, timeout=30)
    response.raise_for_status()
    match = re.search("/abfallberatung/abfuhrkalender-(\\d{4})", response.text)
    if match:
        return match.group(1)
    return str(date.today().year)


def _parse_xlsx(
    response: Any, zone_letter: str, sub_number: str, source: BaseSource
) -> list[dict]:
    """Parse the Dateneingabe sheet from an xlsx file for the given zone."""
    collections: list[dict] = []
    # Raw serials (dates=False): column A holds the collection date as an
    # Excel serial number.
    grid = XlsxParser(sheet="Dateneingabe", dates=False)(response, source)
    for row in grid[1:]:
        vals = row + [None] * (_MAX_COLS - len(row))
        if not vals[0] or vals[2] != zone_letter:
            continue
        try:
            serial = int(float(vals[0]))
        except (ValueError, TypeError):
            continue
        event_date = _EXCEL_EPOCH + timedelta(days=serial)
        for col_idx, waste_name in WASTE_COLUMNS.items():
            col_val = vals[col_idx]
            if col_val and sub_number in str(col_val):
                collections.append({"date": event_date, "type": waste_name})
    return collections


def _retrieve(source: BaseSource) -> Any:
    if not source.params["street"] and (not source.params["zone"]):
        raise SourceArgumentRequired(
            "street or zone", "Either 'street' or 'zone' must be provided."
        )
    year = _discover_year(source.session)
    zone: str
    if source.params["street"] is not None:
        dir_url = _STREET_DIR_URL.format(year=year)
        resp = source.session.get(dir_url, timeout=30)
        resp.raise_for_status()
        directory = resp.json()
        street_key = (
            next((k for k in directory[0].keys() if k != "gebiet"), None)
            if directory
            else None
        )
        if street_key is None:
            raise ValueError("Unexpected street directory format")
        match = next(
            (
                entry
                for entry in directory
                if entry[street_key] == source.params["street"]
            ),
            None,
        )
        if match is None:
            all_streets = sorted(
                entry[street_key] for entry in directory if street_key in entry
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "street", source.params["street"], all_streets
            )
        zone = match["gebiet"].upper()
    else:
        zone = str(source.params["zone"]).upper()
        if zone not in VALID_ZONES:
            raise SourceArgumentNotFoundWithSuggestions("zone", zone, VALID_ZONES)
    zone_letter = zone[0]
    sub_number = zone[1]
    xlsx_url = _XLSX_URL.format(year=year, zone=zone)
    resp = source.session.get(xlsx_url, timeout=60)
    resp.raise_for_status()
    return (resp, zone_letter, sub_number)


def _parse(source: BaseSource, raw) -> list[dict[str, Any]]:
    resp, zone_letter, sub_number = raw
    return _parse_xlsx(resp, zone_letter, sub_number, source)


class CalendarRetriever(RetrieverFunc):
    """Retrieve the calendar and context needed to interpret it."""

    def __call__(self, source: BaseSource) -> Any:
        return _retrieve(source)


class CalendarParser(Parser[list[dict[str, Any]]]):
    """Read provider records without classifying their waste types."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        return _parse(source, response)
