"""Source for Amarsul, Portugal.

Amarsul publishes its selective-collection calendars as single-page PDFs whose
page is one embedded JPEG image (no extractable text). The generic
``PdfImageCalendar`` service does the work of extracting the image, detecting the
month grid and reading the colour-filled day cells; this module only supplies the
Amarsul specifics:

* teal month-header bars (used to detect the grid),
* blue cells  -> "Papel/Cartão" (paper / cardboard),
* yellow cells -> "Embalagens"  (lightweight packaging).

The year is read from the PDF URL, so the schedule is parsed live rather than
hardcoded.
"""

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.service.PdfImageCalendar import (
    ColourBin,
    PdfImageCalendar,
)

TITLE = "Amarsul"
DESCRIPTION = "Source for Amarsul selective-collection calendars, Portugal."
URL = "https://www.amarsul.pt"
COUNTRY = "pt"

# A real, confirmed circuit calendar (circuits D230A/D231A/D249A-D254A, 2026).
EXAMPLE_CALENDAR_URL = (
    "https://www.amarsul.pt/media/orllbvsf/"
    "calend%C3%A1rio-recolhas-2026-d230a-d231a-d249a-d250a-d251a-d252a-d253a-e-d254a.pdf"
)

TEST_CASES = {
    "Circuits D230A-D254A (2026)": {"calendar_url": EXAMPLE_CALENDAR_URL},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find the collection calendar (PDF) for your circuit on the Amarsul "
        "website (https://www.amarsul.pt) and copy the direct link to the PDF "
        "file. Each circuit has its own calendar PDF."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {"calendar_url": "Calendar PDF URL"},
}
PARAM_DESCRIPTIONS = {
    "en": {
        "calendar_url": (
            "Direct link to the Amarsul collection-calendar PDF for your circuit."
        ),
    },
}

# Blue = paper/cardboard, Yellow = lightweight packaging.
TYPE_PAPER = "Papel/Cartão"
TYPE_PACKAGING = "Embalagens"

ICON_MAP = {
    TYPE_PAPER: Icons.PAPER,
    TYPE_PACKAGING: Icons.PLASTIC_PACKAGING,
}


def _is_blue(r: int, g: int, b: int) -> bool:
    return b > 120 and b > r + 40 and b > g + 20 and r < 120


def _is_yellow(r: int, g: int, b: int) -> bool:
    return r > 180 and g > 150 and b < 120


def _is_teal(r: int, g: int, b: int) -> bool:
    # Dark-teal month-header bar, RGB ~= (3, 74, 96).
    return abs(r - 3) < 45 and abs(g - 74) < 45 and abs(b - 96) < 45


class Source:
    def __init__(self, calendar_url: str):
        if not calendar_url:
            raise SourceArgumentRequired(
                "calendar_url", "a calendar PDF URL is required"
            )
        self._url = calendar_url
        self._calendar = PdfImageCalendar(
            header_matches=_is_teal,
            bins=[
                ColourBin(TYPE_PAPER, ICON_MAP[TYPE_PAPER], _is_blue),
                ColourBin(TYPE_PACKAGING, ICON_MAP[TYPE_PACKAGING], _is_yellow),
            ],
        )

    def fetch(self) -> list[Collection]:
        return self._calendar.fetch(self._url)
