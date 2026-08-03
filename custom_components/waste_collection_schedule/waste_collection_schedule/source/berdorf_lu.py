"""Gemeng Bäertref (Berdorf), Luxembourg.

Demonstrates: a yearly calendar PDF whose URL rotates (opaque hashed path on a
third-party host) but is always linked from a stable landing page, so
``PdfLinkRetriever`` finds the current year's PDF instead of a hardcoded URL
that would break every January. The PDF itself is a fixed 2-page grid (page 0
Jan-Jun, page 1 Jul-Dec) with no month headers, which is exactly what
``PdfTextCalendar.DayGridCalendarParser`` reads: the month advances when the day
number resets. Each grid cell names its waste types in free text
(German/French), so the commune's vocabulary is passed in as ``LabelRule``s and
matched to labels that ``ICSTransformer`` maps onto canonical WasteTypes; labels
with no canonical equivalent (a textile round, the mixed organic-and-inert
round) are preserved verbatim. An ``ExtraDatesRule`` backfills SuperDrecksKëscht
(hazardous) dates listed in the info-text, which the coloured calendar overlay
can hide in the grid.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.service.PdfTextCalendar import (
    GERMAN_WEEKDAYS,
    DayGridCalendarParser,
    ExtraDatesRule,
    LabelRule,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import HAZARDOUS, RECYCLABLES

_DATA_URL = "https://www.berdorf.lu/service-citoyens/dechets"

# The PDF filename carries the calendar year: "offallkalenner-2026.pdf".
_PDF_PATTERN = r"offallkalenner-(\d{4})\.pdf"

_SDK = "SuperDrecksKëscht"


@final
class Source(BaseSource):
    TITLE = "Gemeng Bäertref"
    DESCRIPTION = (
        "Source for Berdorf commune (Gemeng Bäertref) waste collection schedule, "
        "Luxembourg."
    )
    URL = "https://www.berdorf.lu"
    COUNTRY = "lu"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Berdorf": {},
    }

    retrieve = PdfLinkRetriever(index_url=_DATA_URL, pattern=_PDF_PATTERN)

    parse = DayGridCalendarParser(
        # The commune writes each round in German, French, or both.
        labels=[
            LabelRule("Hausmüll", r"H\.müll|D\.men\."),
            LabelRule("Biotonne", r"\bBio\b"),
            LabelRule("Glas", r"Glas|verre"),
            LabelRule("Papier", r"[Pp]apier"),
            LabelRule("PMC", r"PMC"),
            LabelRule("Organische und inerte Abfälle", r"Org\.&inert|D\.org\.&inertes"),
            LabelRule("Sperrmüll", r"Sperrmüll|D\.encombrants"),
            LabelRule(_SDK, rf"{_SDK}|\bSDK\b"),
            LabelRule("Altkleidersammlung", r"Kleiders"),
        ],
        year_pattern=_PDF_PATTERN,
        weekdays=GERMAN_WEEKDAYS,
        extra_dates=[
            ExtraDatesRule(_SDK, r"SuperDrecksK[eë]scht.*?Termine:?\s*([\d.,\s]+)"),
        ],
    )

    transform = ICSTransformer(
        type_value_map={
            "PMC": RECYCLABLES,
            _SDK: HAZARDOUS,
        }
    )
