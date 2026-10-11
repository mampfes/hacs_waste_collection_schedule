"""Kainbach bei Graz, Austria.

The municipality publishes its collection calendar as a yearly text PDF
("Abfuhrkalender") linked from its waste page, and posts next year's calendar
while the current one is still running (the 2027 PDF went up in October 2026).
``retrievers.yearly_links`` therefore lists every calendar from this year on and
``FanOutRetriever`` downloads each, so the rest of this year is not dropped when
next year's appears. The file names differ from year to year
("8010-Kainbach_bei_Graz_2026.pdf", "Abfuhrkalender2027.pdf"); both end in the
year, which is also what dates the grid.

Each PDF is the usual two-page day grid (one line per day, "14 Mi B"), read by
``PdfTextCalendar.DayGridCalendarParser``. The cells print short codes glued
together ("BB1GB" is Bioabfall, Bioabfall 4-weekly and bin cleaning), which the
parser's ``codes`` table splits. The printed weekdays are checked against the
calendar year, so a PDF that does not fit the year in its file name fails
loudly instead of returning shifted dates.

The calendar has no per-household selector: households with a 4-weekly
organic (B1) or 8-weekly residual (R1) bin are collected only on the days
printed with that code, and the reduced rounds always coincide with a full
round. Both map to the same canonical type, so the raw label is carried and
duplicates are merged by default.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfTextCalendar import (
    GERMAN_WEEKDAY_ORDER,
    DayGridCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://www.kainbach.gv.at/abfallwirtschaft-m%C3%BCll"

# The calendar file name carries the year it covers, right before ".pdf".
_YEAR_PATTERN = r"(20\d\d)\.pdf$"
_PDF_PATTERN = r"(?:kainbach|abfuhrkalender)[^/]*?(20\d\d)\.pdf$"

# "5 Mo 2" (week number), "14 Mi B", "29 Mo 13Ostermontag".
_LINE_PATTERN = r"^(\d{1,2})\s+([A-Za-z]{2})\b\s*(.*)"

_ORGANIC_REDUCED = "Bioabfall 4-wöchentlich"
_RESIDUAL_REDUCED = "Restmüll 8-wöchentlich"
_ORGANIC_BIN_CLEANING = "Gefäßreinigung Bioabfall"
_RESIDUAL_BIN_CLEANING = "Gefäßreinigung Restmüll"
_PACKAGING = "Leicht- und Metallverpackung"

# The calendar's legend.
_CODES = {
    "B": "Bioabfall",
    "B1": _ORGANIC_REDUCED,
    "GB": _ORGANIC_BIN_CLEANING,
    "R": "Restmüll",
    "R1": _RESIDUAL_REDUCED,
    "GR": _RESIDUAL_BIN_CLEANING,
    "P": "Altpapier",
    "LM": _PACKAGING,
    # Drop-off days at the recycling centre (by appointment). From 2027 the
    # legend reads "Sperrmüll & Problemstoffe" for SM alone.
    "SM": "Sperrmüll",
    "PS": "Problemstoffe",
}


@final
class Source(BaseSource):
    TITLE = "Kainbach bei Graz"
    DESCRIPTION = "Source for Kainbach bei Graz, Austria (Abfuhrkalender PDF)."
    URL = "https://www.kainbach.gv.at"
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Kainbach bei Graz": {},
    }

    PARAMS = ()

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX_URL, pick=retrievers.yearly_links(_PDF_PATTERN)
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        DayGridCalendarParser(
            labels=[],
            codes=_CODES,
            line_pattern=_LINE_PATTERN,
            year_pattern=_YEAR_PATTERN,
            weekday_order=GERMAN_WEEKDAY_ORDER,
        )
    )
    transform = ICSTransformer(
        type_value_map={
            _ORGANIC_REDUCED: wt.ORGANIC,
            _RESIDUAL_REDUCED: wt.GENERAL_WASTE,
            _PACKAGING: wt.RECYCLABLES,
            _ORGANIC_BIN_CLEANING: wt.OTHER,
            _RESIDUAL_BIN_CLEANING: wt.OTHER,
        },
        carry_raw_label=True,
    )
