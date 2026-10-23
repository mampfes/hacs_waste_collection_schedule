"""Gmina Osielsko, Poland.

The municipality links one yearly PDF per collection area ("rejon", 1-9) and
building type from its waste page:
``rejon_8_jednorodzinna_2026.pdf`` (detached houses) and
``rejon_8_wielorodzinna_2026.pdf`` (multi-family buildings). The source keeps
the configured area's calendars from this year on.

Each PDF is a one-page table: a month name down the left and one column per
round, each cell listing that month's collection days ("01, 15, 29", "12*" for
a day moved by a holiday), read by ``PdfMonthRows``. Several rounds share one
column (detached houses: bio waste, paper and metals/plastics; multi-family
buildings: mixed and bio waste, and paper and metals/plastics), so a cell's
dates count for each. A few long
month names ("październik") sit a few points off their data row, so the rows
are clustered with a slightly wider tolerance.
"""

from typing import Any, ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, district
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://osielsko.pl/odpady-komunalne.html"

# The column headings, as printed. The three rounds sharing one column print
# their headings stacked; whole heading lines are matched where they differ in
# width, so that a heading's span covers the column the shared cell sits in.
_TYPES = {
    "Odpady zmieszane (pojemniki)": wt.GENERAL_WASTE,
    "Bioodpady (worki)": wt.ORGANIC,
    "Bioodpady (worki i pojemniki)": wt.ORGANIC,
    "Papier (worki lub pojemniki)": wt.PAPER,
    "Metale, tworzywa sztuczne": wt.RECYCLABLES,
    "Szkło (worki lub pojemniki)": wt.GLASS,
    "Odpady wielkogabarytowe": wt.BULKY_WASTE,
    "Choinki naturalne": wt.GARDEN_WASTE,
}


def _pattern(rejon: Any, multi_family: Any = False, **_: Any) -> str:
    building = "wielo" if multi_family else "jedno"
    return rf"/rejon_{str(rejon).strip()}_{building}rodzinna_(20\d\d)\.pdf$"


@final
class Source(BaseSource):
    TITLE = "Gmina Osielsko"
    DESCRIPTION = "Source for Gmina Osielsko, Poland."
    URL = "https://osielsko.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rejon 8 (Zoledowo)": {"rejon": "8"},
        "Rejon 1 multi-family": {"rejon": "1", "multi_family": True},
    }

    PARAMS = (
        district("rejon"),
        boolean("multi_family", default=False),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your collection area number (rejon, 1-9) as listed on "
            "https://osielsko.pl/odpady-komunalne.html (e.g. '8' for "
            "Żołędowo, Strzelce Leśne and Bożenkowo). Tick 'multi_family' for "
            "a multi-family building (zabudowa wielorodzinna)."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_INDEX_URL, pick=retrievers.yearly_links(_pattern)),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.PdfTableParser(y_tolerance=4.0, min_words=30),
        then=preprocessors.PdfMonthRows(
            labels=_TYPES, year_pattern=r"od \d{2}\.\d{2}\.(20\d\d)"
        ),
    )
    transform = ICSTransformer(type_value_map=_TYPES)
