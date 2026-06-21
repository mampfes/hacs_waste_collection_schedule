"""Source for Amarsul, Portugal.

Amarsul publishes its selective-collection calendars as single-page PDFs whose
page is one embedded JPEG image (no extractable text). The reusable
``PdfImageRetriever`` + ``ColourGridCalendarParser`` pipeline steps do the work
of extracting the image, detecting the 3x4 month grid and reading the
colour-filled day cells; this module only supplies the Amarsul specifics:

* teal month-header bars (used to detect the grid),
* blue cells  -> paper / cardboard (Papel/Cartao),
* yellow cells -> lightweight packaging (Embalagens).

The year is read from the PDF URL, so the schedule is parsed live rather than
hardcoded.
"""

from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.PdfImageCalendar import (
    ColourBin,
    ColourGridCalendarParser,
    PdfImageRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import PAPER, RECYCLABLES

# Cell labels (mapped to canonical waste types by the transformer below).
PAPER_LABEL = "Papel/Cartao"
PACKAGING_LABEL = "Embalagens"


def _is_blue(r: int, g: int, b: int) -> bool:
    return b > 120 and b > r + 40 and b > g + 20 and r < 120


def _is_yellow(r: int, g: int, b: int) -> bool:
    return r > 180 and g > 150 and b < 120


def _is_teal(r: int, g: int, b: int) -> bool:
    # Dark-teal month-header bar, RGB ~= (3, 74, 96).
    return abs(r - 3) < 45 and abs(g - 74) < 45 and abs(b - 96) < 45


@final
class Source(BaseSource):
    TITLE = "Amarsul"
    DESCRIPTION = "Source for Amarsul selective-collection calendars, Portugal."
    URL = "https://www.amarsul.pt"
    COUNTRY = "pt"
    CODEOWNERS = ["@markvp"]

    # A real, confirmed circuit calendar (circuits D230A/D231A/D249A-D254A, 2026).
    _EXAMPLE_CALENDAR_URL = (
        "https://www.amarsul.pt/media/orllbvsf/"
        "calend%C3%A1rio-recolhas-2026-d230a-d231a-d249a-d250a-d251a-d252a-d253a-e-d254a.pdf"
    )

    TEST_CASES = {
        "Circuits D230A-D254A (2026)": {"calendar_url": _EXAMPLE_CALENDAR_URL},
    }

    PARAMS = [text_field("calendar_url", "Calendar PDF URL")]

    HOWTO = {
        "en": (
            "Find the collection calendar (PDF) for your circuit on the Amarsul "
            "website (https://www.amarsul.pt) and copy the direct link to the PDF "
            "file. Each circuit has its own calendar PDF."
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = PdfImageRetriever(url_param="calendar_url")

    parse = ColourGridCalendarParser(
        header_matches=_is_teal,
        bins=[
            ColourBin(PAPER_LABEL, _is_blue),
            ColourBin(PACKAGING_LABEL, _is_yellow),
        ],
        box_cols=3,
        # Amarsul's narrow month-name text can defeat run detection on some
        # circuits, so keep the calibrated width-scaled fallback.
        fallback_box_x=(73, 449, 824),
        fallback_box_w=353,
    )

    transformer = ICSTransformer(
        type_value_map={
            PAPER_LABEL: PAPER,
            PACKAGING_LABEL: RECYCLABLES,
        }
    )

    def __init__(self, calendar_url: str):
        super().__init__(calendar_url=calendar_url)
