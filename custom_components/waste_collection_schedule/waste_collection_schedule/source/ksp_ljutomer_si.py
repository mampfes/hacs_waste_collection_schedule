"""KSP Ljutomer, Slovenia.

Komunalno stanovanjsko podjetje Ljutomer collects household waste in the
municipalities of Apače, Križevci, Ljutomer, Razkrižje and Veržej, and
publishes one yearly calendar PDF per municipality (Ljutomer: one per collection
weekday) on a stable page. The file names carry the year, and moved it between
2025 ("KOLEDAR-LJUTOMER-TOREK-2025.pdf") and 2026
("KOLEDAR-2026-LJUTOMER-TOREK.pdf"), so the link pattern accepts both and
``retrievers.yearly_links`` keeps the calendars from this year on.

Each PDF is one table: a row per month, a column per waste round, the days of
the month listed in each cell ("6., 20."). ``preprocessors.PdfMonthRows`` reads
it by position; holiday moves are printed as footnotes ("2. januar se nadomešča
3. januarja") and applied to the dates the table prints.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import lookups, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = (
    "https://ksp-ljutomer.si/dejavnosti/ravnanje-z-odpadki/"
    "koledarji-zbiranja-komunalnih-odpadkov/"
)

# Calendar choice -> the name its PDF carries.
_CALENDARS = {
    "Apače": "APACE",
    "Križevci": "KRIZEVCI",
    "Ljutomer (torek)": "LJUTOMER-TOREK",
    "Ljutomer (sreda)": "LJUTOMER-SREDA",
    "Ljutomer (četrtek)": "LJUTOMER-CETRTEK",
    "Razkrižje": "RAZKRIZJE",
    "Veržej": "VERZEJ",
}


def _pdf_pattern(calendar: str, **_) -> str:
    # A YAML value outside the dropdown gets suggestions, not a KeyError.
    name = re.escape(
        lookups.resolve(
            _CALENDARS,
            calendar,
            argument="calendar",
            normalize=lookups.normalize_loose,
        )
    )
    return rf"/KOLEDAR-(?:(20\d\d)-)?{name}(?:-(20\d\d))?\.pdf$"


# The column headings, as printed (one word of each suffices).
_TYPES = {
    "KOMUNALNI": wt.GENERAL_WASTE,
    "EMBALAŽA": wt.RECYCLABLES,
    "PAPIR": wt.PAPER,
    "STEKLO": wt.GLASS,
    "BIOLOŠKI": wt.ORGANIC,
}

# "2. januar se nadomešča 3. januarja", "1. januar se nadomešča 30. decembra 2025"
_MOVED = (
    r"(?P<from_day>\d{1,2})\.\s*(?P<from_month>[^\W\d_]+)\s+se\s+nadome[šs][čc]a\s+"
    r"(?P<to_day>\d{1,2})\.\s*(?P<to_month>[^\W\d_]+)(?:\s+(?P<to_year>20\d\d))?"
)


@final
class Source(BaseSource):
    TITLE = "KSP Ljutomer"
    DESCRIPTION = (
        "Source for KSP Ljutomer (Apače, Križevci, Ljutomer, Razkrižje, Veržej), "
        "Slovenia."
    )
    URL = "https://ksp-ljutomer.si"
    COUNTRY = "si"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ljutomer torek": {"calendar": "Ljutomer (torek)"},
        "Ljutomer cetrtek": {"calendar": "Ljutomer (četrtek)"},
        "Apace": {"calendar": "Apače"},
    }

    PARAMS = (dropdown("calendar", list(_CALENDARS), label="Calendar"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose your municipality. In Ljutomer the calendar depends on the "
            "collection weekday; each calendar on "
            "https://ksp-ljutomer.si/dejavnosti/ravnanje-z-odpadki/"
            "koledarji-zbiranja-komunalnih-odpadkov/ lists the settlements and "
            "streets it covers."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX_URL, pick=retrievers.yearly_links(_pdf_pattern)
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    # Each year's PDF on its own: the year is printed once, in its heading.
    parse = parsers.EachResponse(
        parsers.PdfTableParser(min_words=30),
        then=preprocessors.PdfMonthRows(
            labels=_TYPES, year_pattern=r"LETO\s+(20\d\d)", moved_pattern=_MOVED
        ),
    )
    transform = ICSTransformer(type_value_map=_TYPES)
