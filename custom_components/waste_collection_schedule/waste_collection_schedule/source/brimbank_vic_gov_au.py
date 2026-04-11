import calendar as cal_mod
import logging
import re
from datetime import date, timedelta
from io import BytesIO

import requests
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTCurve, LTLayoutContainer, LTRect, LTTextBox
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Brimbank City Council"
DESCRIPTION = "Source for Brimbank City Council waste collection."
URL = "https://www.brimbank.vic.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Monday A": {"day": "Monday", "calendar": "A"},
    "Friday B": {"day": "Friday", "calendar": "B"},
    "Wednesday A": {"day": "Wednesday", "calendar": "A"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "day": "Your collection day (Monday to Friday). Check the map on the back of the waste calendar PDF.",
        "calendar": "Your calendar cycle (A or B). Check the map on the back of the waste calendar PDF.",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "day": "Collection day",
        "calendar": "Calendar cycle",
    }
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food & Garden Organics": "mdi:leaf",
}

PDF_URL = (
    "https://serviceapi.brimbank.vic.gov.au/CMServiceAPI/Record/7854806/file/document"
)

# Color thresholds for PDF parsing (RGB float tuples)
_GREEN = (0.584, 0.795, 0.392)
_YELLOW = (1.0, 0.888, 0.312)
_RED = (0.818, 0.408, 0.361)
_COLOR_TOL = 0.15

# Calendar grid layout constants
_MONTH_COL_X = [(87, 167), (167, 247), (247, 326), (326, 406)]
_CAL_A_ROW_Y = [66, 142, 219]
_CAL_B_ROW_Y = [314, 391, 467]
_MONTHS_PER_ROW = [
    [(2, 2026), (3, 2026), (4, 2026), (5, 2026)],
    [(6, 2026), (7, 2026), (8, 2026), (9, 2026)],
    [(10, 2026), (11, 2026), (12, 2026), (1, 2027)],
]

_WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}

_LOGGER = logging.getLogger(__name__)


def _color_match(c, target):
    if not c or not isinstance(c, tuple) or len(c) != 3:
        return False
    return all(abs(c[i] - target[i]) < _COLOR_TOL for i in range(3))


def _classify_color(fill):
    if _color_match(fill, _GREEN):
        return "FOGO"
    if _color_match(fill, _YELLOW):
        return "RECYCLE"
    if _color_match(fill, _RED):
        return "NONE"
    return None


def _iter_elements(container):
    for el in container:
        yield el
        if isinstance(el, LTLayoutContainer):
            yield from _iter_elements(el)


def _parse_pdf(pdf_bytes):
    """Parse the Brimbank waste calendar PDF and return (schedule_a, schedule_b).

    Each schedule is a dict mapping date -> 'RECYCLE' | 'FOGO' | 'NONE'.
    Only weekday dates (Mon-Fri) plus holiday-shifted Saturdays are included.
    """
    pages = list(extract_pages(BytesIO(pdf_bytes), laparams=LAParams()))
    if not pages:
        raise ValueError("PDF contains no pages")

    page = pages[0]
    ph = page.height

    # Collect colored curve cells
    colored_cells = []
    for el in _iter_elements(page):
        if isinstance(el, LTCurve) and not isinstance(el, LTRect):
            fill = el.non_stroking_color
            if fill and isinstance(fill, tuple) and len(fill) == 3:
                label = _classify_color(fill)
                if label:
                    x0, y0, x1, y1 = el.bbox
                    colored_cells.append(
                        {
                            "color": label,
                            "cx": (x0 + x1) / 2,
                            "cy": ph - (y0 + y1) / 2,
                        }
                    )

    # Parse day number text boxes
    day_boxes = []
    for el in page:
        if isinstance(el, LTTextBox):
            x0, y0, x1, y1 = el.bbox
            top = ph - y1
            text = el.get_text().strip()
            nums = re.findall(r"\d+", text)
            if nums and all(1 <= int(n) <= 31 for n in nums):
                day_boxes.append(
                    {"nums": [int(n) for n in nums], "x0": x0, "x1": x1, "top": top}
                )

    def build_schedule(row_y_starts):
        schedule = {}
        for row_idx, row_y in enumerate(row_y_starts):
            for col_idx, (month, year) in enumerate(_MONTHS_PER_ROW[row_idx]):
                mx0, mx1 = _MONTH_COL_X[col_idx]
                days_in_month = cal_mod.monthrange(year, month)[1]

                month_boxes = [
                    b
                    for b in day_boxes
                    if b["x0"] >= mx0 - 5
                    and b["x1"] <= mx1 + 5
                    and row_y + 5 < b["top"] < row_y + 80
                ]

                for box in month_boxes:
                    col_width = (box["x1"] - box["x0"]) / 7
                    for day_num in box["nums"]:
                        if day_num < 1 or day_num > days_in_month:
                            continue
                        d = date(year, month, day_num)
                        # Skip Sun (6) and Sat (5) unless it's a holiday shift
                        if d.weekday() == 6:  # Sunday
                            continue

                        # Grid column: Sun=0, Mon=1 ... Sat=6
                        grid_col = (d.weekday() + 1) % 7
                        day_cx = box["x0"] + (grid_col + 0.5) * col_width
                        day_cy = box["top"] + 3

                        best = None
                        best_dist = 999
                        for cell in colored_cells:
                            dx = abs(cell["cx"] - day_cx)
                            dy = abs(cell["cy"] - day_cy)
                            dist = (dx**2 + dy**2) ** 0.5
                            if dist < best_dist and dist < 10:
                                best_dist = dist
                                best = cell

                        if best:
                            schedule[d] = best["color"]

        # Remove spurious Saturday entries that aren't holiday shifts
        # A Saturday is only valid if the preceding Friday is NONE (holiday)
        to_remove = []
        for d, color in schedule.items():
            if d.weekday() == 5:  # Saturday
                friday = d - timedelta(days=1)
                if schedule.get(friday) != "NONE":
                    to_remove.append(d)
        for d in to_remove:
            del schedule[d]

        return schedule

    schedule_a = build_schedule(_CAL_A_ROW_Y)
    schedule_b = build_schedule(_CAL_B_ROW_Y)
    return schedule_a, schedule_b


class Source:
    def __init__(self, day: str, calendar: str):
        day_lower = day.strip().lower()
        if day_lower not in _WEEKDAY_MAP:
            raise ValueError(
                f"Invalid day '{day}'. Must be one of: Monday, Tuesday, Wednesday, Thursday, Friday"
            )
        self._weekday = _WEEKDAY_MAP[day_lower]
        self._day_name = day_lower

        cal_upper = calendar.strip().upper()
        if cal_upper not in ("A", "B"):
            raise ValueError(f"Invalid calendar '{calendar}'. Must be A or B")
        self._calendar = cal_upper

    def fetch(self):
        r = requests.get(PDF_URL, timeout=30)
        r.raise_for_status()

        schedule_a, schedule_b = _parse_pdf(r.content)
        schedule = schedule_a if self._calendar == "A" else schedule_b

        entries = []
        for d, color in sorted(schedule.items()):
            # Skip NONE dates (holidays with no collection)
            if color == "NONE":
                continue

            # Check if this date is for the user's collection day
            if d.weekday() == self._weekday:
                # Regular collection day
                entries.append(
                    Collection(
                        date=d, t="General Waste", icon=ICON_MAP["General Waste"]
                    )
                )
                if color == "RECYCLE":
                    entries.append(
                        Collection(date=d, t="Recycling", icon=ICON_MAP["Recycling"])
                    )
                elif color == "FOGO":
                    entries.append(
                        Collection(
                            date=d,
                            t="Food & Garden Organics",
                            icon=ICON_MAP["Food & Garden Organics"],
                        )
                    )
            elif d.weekday() == 5:  # Saturday (holiday shift)
                # This is a shifted collection for Friday users
                if self._weekday == 4:  # Friday
                    entries.append(
                        Collection(
                            date=d,
                            t="General Waste",
                            icon=ICON_MAP["General Waste"],
                        )
                    )
                    if color == "RECYCLE":
                        entries.append(
                            Collection(
                                date=d, t="Recycling", icon=ICON_MAP["Recycling"]
                            )
                        )
                    elif color == "FOGO":
                        entries.append(
                            Collection(
                                date=d,
                                t="Food & Garden Organics",
                                icon=ICON_MAP["Food & Garden Organics"],
                            )
                        )

        return entries
