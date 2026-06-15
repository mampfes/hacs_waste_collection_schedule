"""Source for Amarsul, Portugal.

Amarsul publishes its selective-collection calendars as single-page PDFs whose
page is one embedded JPEG image (no extractable text). This source downloads the
PDF, extracts the embedded image, and reads the yearly grid by detecting the
colour-filled day cells:

* blue cells  -> "Papel/Cartão" (paper / cardboard)
* yellow cells -> "Embalagens"  (lightweight packaging)

The grid geometry is derived from the teal month-header bars, so the parser does
not depend on any hardcoded schedule -- only the year (read from the PDF URL) is
needed to map each (weekday-column, week-row) position to a real date.
"""

import calendar
import re
from datetime import date
from io import BytesIO
from typing import List, Optional

import requests
from PIL import Image
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentRequired,
)

TITLE = "Amarsul"
DESCRIPTION = "Source for Amarsul selective-collection calendars, Portugal."
URL = "https://www.amarsul.pt"
COUNTRY = "pt"

# A real, confirmed circuit calendar (circuits D230A/D231A/D249A-D254A, 2026).
DEFAULT_CALENDAR_URL = (
    "https://www.amarsul.pt/media/orllbvsf/"
    "calend%C3%A1rio-recolhas-2026-d230a-d231a-d249a-d250a-d251a-d252a-d253a-e-d254a.pdf"
)

TEST_CASES = {
    "Circuits D230A-D254A (2026)": {"calendar_url": DEFAULT_CALENDAR_URL},
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

# --- Image-grid calibration (relative to the 1240x1744 extracted JPEG) ------
# The calendar is a 3-column x 4-row arrangement of month mini-calendars,
# laid out row-major: Jan-Mar (top row) ... Oct-Dec (bottom row).
_BOX_X = (73, 449, 824)  # left edge of each month-box column
_BOX_W = 353  # month-box width (7 weekday columns)
_N_COLS = 7  # SEG TER QUA QUI SEX SAB DOM (Mon..Sun)
_N_ROWS = 6  # up to 6 week-rows per month
_ROW1_OFFSET = 71.0  # header-bar top -> centre of first week-row
_ROW_PITCH = 29.4  # vertical spacing between week-rows
_REF_WIDTH = 1240  # reference image width the calibration was measured on


def _is_blue(r: int, g: int, b: int) -> bool:
    return b > 120 and b > r + 40 and b > g + 20 and r < 120


def _is_yellow(r: int, g: int, b: int) -> bool:
    return r > 180 and g > 150 and b < 120


def _is_teal(r: int, g: int, b: int) -> bool:
    # Dark-teal month-header bar, RGB ~= (3, 74, 96).
    return abs(r - 3) < 45 and abs(g - 74) < 45 and abs(b - 96) < 45


class Source:
    def __init__(self, calendar_url: Optional[str] = None):
        self._url = calendar_url or DEFAULT_CALENDAR_URL

    def _extract_image(self) -> Image.Image:
        try:
            resp = requests.get(self._url, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise SourceArgumentException(
                "calendar_url", f"could not download the calendar PDF: {exc}"
            ) from exc

        try:
            reader = PdfReader(BytesIO(resp.content))
            page = reader.pages[0]
            images = page.images
            if not images:
                raise SourceArgumentException(
                    "calendar_url", "the PDF page contains no embedded image"
                )
            img = images[0].image
        except SourceArgumentException:
            raise
        except Exception as exc:
            raise SourceArgumentException(
                "calendar_url", f"could not read the calendar PDF: {exc}"
            ) from exc

        return img.convert("RGB")

    def _year(self) -> int:
        match = re.search(r"20\d\d", self._url)
        if match:
            return int(match.group(0))
        return date.today().year

    def _header_tops(self, img: Image.Image) -> List[int]:
        """Locate the 4 teal month-header bands (one per box-row)."""
        width, height = img.size
        px = img.load()
        teal_rows = []
        for y in range(height):
            count = 0
            for x in range(0, width, 2):
                if _is_teal(*px[x, y]):
                    count += 1
            teal_rows.append(count)

        threshold = max(teal_rows) * 0.4
        bands: List[tuple] = []
        start = None
        for y, count in enumerate(teal_rows):
            if count > threshold and start is None:
                start = y
            elif count <= threshold and start is not None:
                if y - start >= 15:  # full header bars are ~28px tall
                    bands.append((start, y))
                start = None
        if start is not None and height - start >= 15:
            bands.append((start, height))

        tops = [b[0] for b in bands]
        if len(tops) != 4:
            raise SourceArgumentException(
                "calendar_url",
                f"expected 4 month-header rows in the calendar image, found {len(tops)}",
            )
        return tops

    def fetch(self) -> List[Collection]:
        if not self._url:
            raise SourceArgumentRequired(
                "calendar_url", "a calendar PDF URL is required"
            )

        img = self._extract_image()
        width, height = img.size
        px = img.load()
        scale = width / _REF_WIDTH

        header_tops = self._header_tops(img)
        year = self._year()

        box_x = [int(x * scale) for x in _BOX_X]
        box_w = _BOX_W * scale
        row1_offset = _ROW1_OFFSET * scale
        row_pitch = _ROW_PITCH * scale
        # Sampling half-window scaled from the reference cell size.
        half_x = max(4, int(11 * scale))
        half_y = max(5, int(13 * scale))

        def cell_colour(cx: int, cy: int) -> Optional[str]:
            n_blue = n_yellow = 0
            for x in range(cx - half_x, cx + half_x + 1):
                if x < 0 or x >= width:
                    continue
                for y in range(cy - half_y, cy + half_y + 1):
                    if y < 0 or y >= height:
                        continue
                    r, g, b = px[x, y]
                    if _is_blue(r, g, b):
                        n_blue += 1
                    elif _is_yellow(r, g, b):
                        n_yellow += 1
            # Require a clearly filled cell, not anti-aliasing noise.
            threshold = max(40, int(50 * scale * scale))
            if n_blue > threshold or n_yellow > threshold:
                return TYPE_PAPER if n_blue >= n_yellow else TYPE_PACKAGING
            return None

        entries: List[Collection] = []
        for month in range(1, 13):
            box_row = (month - 1) // 3
            box_col = (month - 1) % 3
            htop = header_tops[box_row]
            bx = box_x[box_col]
            first_weekday, days_in_month = calendar.monthrange(year, month)

            for week in range(_N_ROWS):
                cy = int(htop + row1_offset + week * row_pitch)
                for col in range(_N_COLS):
                    cx = int(bx + (col + 0.5) * box_w / _N_COLS)
                    waste_type = cell_colour(cx, cy)
                    if waste_type is None:
                        continue
                    day = week * _N_COLS + col - first_weekday + 1
                    if not 1 <= day <= days_in_month:
                        # Geometry sanity guard: skip impossible mappings.
                        continue
                    entries.append(
                        Collection(
                            date=date(year, month, day),
                            t=waste_type,
                            icon=ICON_MAP[waste_type],
                        )
                    )

        if not entries:
            raise SourceArgumentException(
                "calendar_url",
                "no collection days could be detected in the calendar image",
            )

        return entries
