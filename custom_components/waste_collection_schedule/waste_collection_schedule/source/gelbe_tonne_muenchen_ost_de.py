import difflib
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import RowTransformer

# The calendar page is a Vue app without a backend API. All data ships inside
# one script: a CSV "Bezirk;Straße;Bemerkung" mapping streets (or house number
# ranges) to one of the collection districts, and an iCalendar whose events
# carry the district number as SUMMARY.
CALENDAR_PAGE_URL = "https://www.gelbe-tonne-muenchen-ost.de/abfuhrkalender"
SCRIPT_URL = "https://www.gelbe-tonne-muenchen-ost.de/fileadmin/abfuhrkalender-gelbetonne/abfuhrkalender.js"
_SCRIPT_LINK = r'src="([^"]*/abfuhrkalender-gelbetonne/abfuhrkalender\.js[^"]*)"'

# The bundle also holds a short "BEGIN:VCALENDAR" literal in its ICS export
# code; requiring the line break that follows it selects the data literal.
_STREETS = r'("Bezirk;Stra(?:\\.|[^"\\])*")'
_CALENDAR = r'("BEGIN:VCALENDAR\\r?\\n(?:\\.|[^"\\])*")'

_COMPLETE = "Komplett"
_LABEL = "Gelbe Tonne"
_HOUSE_NUMBER = re.compile(r"^\s*(\d+)\s*([a-z]?)\s*$", re.IGNORECASE)


def _house_number(value: str) -> tuple[int, str] | None:
    match = _HOUSE_NUMBER.match(value)
    if match is None:
        return None
    return int(match.group(1)), match.group(2).lower()


def _in_range(spec: str, number: tuple[int, str]) -> bool:
    """Match a house number against a range such as ``1-51, 2-46`` or ``8``.

    Each comma-separated part is one side of the street: its parity comes from
    the first number. An upper bound that is not a number is open-ended:
    "Ende", which the provider data also contains misspelt once.
    """
    for part in spec.split(","):
        lower, _, upper = part.strip().partition("-")
        start = _house_number(lower)
        if start is None:
            continue
        if not upper:
            if number[0] == start[0] and (not start[1] or number[1] == start[1]):
                return True
            continue
        if number[0] % 2 != start[0] % 2 or number < start:
            continue
        end = _house_number(upper)
        if end is None or number <= (end[0], end[1] or "z"):
            return True
    return False


def _normalise(name: str) -> str:
    name = name.lower().replace("straße", "str.").replace("strasse", "str.")
    return re.sub(r"[\s.\-]", "", name)


def _district(streets: str, street: str, house_number: str | None) -> int:
    rows = []
    for line in streets.lstrip("﻿").splitlines()[1:]:
        fields = [field.strip() for field in line.split(";")]
        if len(fields) == 3 and fields[0].isdigit() and fields[1]:
            rows.append((int(fields[0]), fields[1], fields[2]))

    matches = [row for row in rows if row[1] == street] or [
        row for row in rows if _normalise(row[1]) == _normalise(street)
    ]
    if not matches:
        names = sorted({row[1] for row in rows})
        raise SourceArgumentNotFoundWithSuggestions(
            "street",
            street,
            difflib.get_close_matches(street, names, n=10, cutoff=0.6) or names,
        )
    if len(matches) == 1 and matches[0][2] == _COMPLETE:
        return matches[0][0]

    ranges = [row[2] for row in matches]
    if not house_number:
        raise SourceArgumentRequiredWithSuggestions(
            "house_number",
            "the street is split between collection districts",
            ranges,
        )
    for district, _, spec in matches:
        if spec == house_number:
            return district
    number = _house_number(house_number)
    if number is not None:
        hits = [row for row in matches if _in_range(row[2], number)]
        if len({row[0] for row in hits}) == 1:
            return hits[0][0]
        if hits:
            # the provider data assigns a few numbers to two districts
            raise SourceArgAmbiguousWithSuggestions(
                "house_number", house_number, [row[2] for row in hits]
            )
    raise SourceArgumentNotFoundWithSuggestions("house_number", house_number, ranges)


def _collections(record, source):
    district = _district(
        record["streets"],
        source.params["street"],
        source.params["house_number"],
    )
    rows = [
        (day, _LABEL)
        for day, summary in ICS().convert(record["calendar"])
        if summary.strip() == str(district)
    ]
    if not rows:
        raise SourceArgumentNotFound("street", source.params["street"])
    return rows


@final
class Source(BaseSource):
    TITLE = "Gelbe Tonne München-Ost (Knettenbrech + Gurdulic)"
    DESCRIPTION = "Source for the Gelbe Tonne in eastern Munich, collected by Knettenbrech + Gurdulic."
    URL = "https://www.gelbe-tonne-muenchen-ost.de"
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@OnSerious"]
    TEST_CASES: ClassVar[dict] = {
        "Aachener Str.": {"street": "Aachener Str."},
        "Balanstr. range": {"street": "Balanstr.", "house_number": "53-Ende, 48-Ende"},
        "Chiemgaustr. range": {
            "street": "Chiemgaustr.",
            "house_number": "109-Ende, 114-Ende",
        },
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Balanstr. without house number": {"street": "Balanstr."},
        "Unknown street": {"street": "Balanstrase"},
    }
    PARAMS = (street(), house_number(optional=True))
    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES]
    HOWTO: ClassVar[dict] = {
        "en": "Enter the street as listed at https://www.gelbe-tonne-muenchen-ost.de/abfuhrkalender (e.g. 'Balanstr.'). A house number is only needed for streets split between collection districts; without it the form offers the valid ranges.",
        "de": "Straße wie unter https://www.gelbe-tonne-muenchen-ost.de/abfuhrkalender eingeben (z.B. 'Balanstr.'). Eine Hausnummer ist nur bei Straßen nötig, die auf mehrere Abfuhrbezirke aufgeteilt sind; ohne sie bietet das Formular die gültigen Bereiche an.",
    }
    RAISE_ON_EMPTY = True

    retrieve = retrievers.LinkedAssetRetriever(
        CALENDAR_PAGE_URL, pattern=_SCRIPT_LINK, fallback_url=SCRIPT_URL
    )
    parse = parsers.JsObjectParser({"streets": _STREETS, "calendar": _CALENDAR})
    preprocess = preprocessors.ExplodeList(_collections)
    transform = RowTransformer()
