import logging
import re
from datetime import date
from io import BytesIO
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.generic import ContentStream
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "East Hampshire District Council"
DESCRIPTION = "Waste collection schedules for East Hampshire District Council."
URL = "https://www.easthants.gov.uk"
COUNTRY = "uk"

_SCHEDULE_URL = f"{URL}/bin-collections/find-your-bin-calendar"
_MONTHS = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}
_MONTH_RE = re.compile(r"^(" + "|".join(_MONTHS) + r")\s+(20\d{2})$")
_DATE_RE = re.compile(r"^(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+(\d{1,2})$")
_CALENDAR_LINK_RE = re.compile(r"^Calendar\s+(\d+)\b", re.IGNORECASE)

# RGB fill colours used for the two collection rows in the council PDFs.
_RUBBISH_COLOUR = (0.248, 0.646, 0.209)
_RECYCLING_COLOUR = (0.391, 0.389, 0.387)
_COLOUR_TOLERANCE = 0.02

_TYPE_MAP = {
    "rubbish": "Rubbish",
    "recycling": "Recycling and glass",
}
ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling and glass": Icons.RECYCLING,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "calendar_number": (
            "The bin calendar number assigned to your address, shown on your "
            "existing calendar or on the council's bin calendar map."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "calendar_number": "Calendar number",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar. "
        "Use the map near the bottom of the page to find your address, then enter "
        "the displayed calendar number."
    ),
}

TEST_CASES = {
    "Calendar 16": {"calendar_number": 16},
}


def _colour_matches(
    actual: tuple[float, ...] | None, expected: tuple[float, ...]
) -> bool:
    return bool(
        actual
        and len(actual) >= 3
        and all(
            abs(actual[index] - expected[index]) <= _COLOUR_TOLERANCE
            for index in range(3)
        )
    )


def _calendar_links(html: str) -> dict[int, str]:
    soup = BeautifulSoup(html, "html.parser")
    links: dict[int, str] = {}

    for anchor in soup.find_all("a", href=True):
        label = " ".join(anchor.stripped_strings)
        match = _CALENDAR_LINK_RE.match(label)
        if match:
            links[int(match.group(1))] = urljoin(_SCHEDULE_URL, str(anchor["href"]))

    return links


def _collection_rectangles(page, reader: PdfReader) -> list[tuple]:
    """Return collection-type rectangles as (x0, y0, x1, y1, type_key)."""
    rectangles: list[tuple] = []
    fill_colour: tuple[float, ...] | None = None
    colour_stack: list[tuple[float, ...] | None] = []

    content = ContentStream(page.get_contents(), reader)
    for operands, operator in content.operations:
        if operator == b"q":
            colour_stack.append(fill_colour)
        elif operator == b"Q":
            fill_colour = colour_stack.pop() if colour_stack else None
        elif operator in (b"rg", b"scn") and len(operands) >= 3:
            try:
                fill_colour = tuple(float(value) for value in operands[:3])
            except (TypeError, ValueError):
                fill_colour = None
        elif operator == b"g" and operands:
            try:
                grey = float(operands[0])
            except (TypeError, ValueError):
                fill_colour = None
            else:
                fill_colour = (grey, grey, grey)
        elif operator == b"re" and len(operands) == 4:
            if _colour_matches(fill_colour, _RUBBISH_COLOUR):
                type_key = "rubbish"
            elif _colour_matches(fill_colour, _RECYCLING_COLOUR):
                type_key = "recycling"
            else:
                continue

            try:
                x, y, width, height = (float(value) for value in operands)
            except (TypeError, ValueError):
                continue

            # Date cells are around 53pt wide. On bank-holiday rows the date
            # part is orange, but the adjacent 16-17pt icon cell retains the
            # collection colour. Ignore smaller icon artwork and large legends.
            if not (10 <= abs(width) <= 60 and 10 <= abs(height) <= 16):
                continue

            rectangles.append(
                (
                    min(x, x + width),
                    min(y, y + height),
                    max(x, x + width),
                    max(y, y + height),
                    type_key,
                )
            )

    return rectangles


def _type_at_position(
    rectangles: list[tuple], text_x: float, text_y: float
) -> str | None:
    # Each calendar column is roughly 83pt wide. Looking no more than 70pt to
    # the right includes the bank-holiday icon cell without reaching the next
    # calendar column.
    for x0, y0, x1, y1, type_key in rectangles:
        if y0 - 1 <= text_y <= y1 + 1 and x1 >= text_x - 5 and x0 <= text_x + 70:
            return type_key
    return None


def _normalise_heading_year(
    printed_year: int, month: int, previous: tuple[int, int] | None
) -> int:
    """Correct an inconsistent printed year using the month sequence."""
    if previous is None:
        return printed_year

    previous_year, previous_month = previous
    expected_year = previous_year + int(month < previous_month)
    if printed_year != expected_year:
        _LOGGER.warning(
            "Calendar PDF labels month %d as %d; using %d based on the "
            "surrounding months",
            month,
            printed_year,
            expected_year,
        )
        return expected_year
    return printed_year


def _parse_page(page, reader: PdfReader) -> list[Collection]:
    rectangles = _collection_rectangles(page, reader)
    fragments: list[tuple[str, float, float]] = []

    def collect_text(text, _cm, tm, _font, _font_size):
        cleaned = " ".join(text.split()).upper()
        if cleaned:
            fragments.append((cleaned, float(tm[4]), float(tm[5])))

    page.extract_text(visitor_text=collect_text)

    current_month_by_column: dict[float, tuple[int, int]] = {}
    collections: list[Collection] = []
    unmatched_dates: list[str] = []

    for text, text_x, text_y in fragments:
        column = round(text_x, 1)
        if month_match := _MONTH_RE.fullmatch(text):
            month = _MONTHS[month_match.group(1)]
            printed_year = int(month_match.group(2))
            current_month_by_column[column] = (
                _normalise_heading_year(
                    printed_year, month, current_month_by_column.get(column)
                ),
                month,
            )
            continue

        date_match = _DATE_RE.fullmatch(text)
        if not date_match or column not in current_month_by_column:
            continue

        year, month = current_month_by_column[column]
        collection_date = date(year, month, int(date_match.group(1)))
        type_key = _type_at_position(rectangles, text_x, text_y)
        if type_key is None:
            unmatched_dates.append(collection_date.isoformat())
            continue

        waste_type = _TYPE_MAP[type_key]
        collections.append(
            Collection(collection_date, waste_type, icon=ICON_MAP[waste_type])
        )

    if unmatched_dates:
        raise ValueError(
            "Could not determine collection types for PDF dates: "
            + ", ".join(unmatched_dates)
        )

    return collections


def _parse_pdf(content: bytes) -> list[Collection]:
    reader = PdfReader(BytesIO(content))
    collections: list[Collection] = []
    for page in reader.pages:
        collections.extend(_parse_page(page, reader))

    unique = {(item.date, item.type): item for item in collections}
    return sorted(unique.values(), key=lambda item: (item.date, item.type))


class Source:
    def __init__(self, calendar_number: int):
        try:
            self._calendar_number = int(calendar_number)
        except (TypeError, ValueError) as exc:
            raise SourceArgumentNotFound("calendar_number", calendar_number) from exc

        if self._calendar_number < 1:
            raise SourceArgumentNotFound("calendar_number", calendar_number)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        page_response = session.get(_SCHEDULE_URL, timeout=30)
        page_response.raise_for_status()

        links = _calendar_links(page_response.text)
        if self._calendar_number not in links:
            raise SourceArgumentNotFoundWithSuggestions(
                "calendar_number", self._calendar_number, sorted(links)
            )

        pdf_response = session.get(links[self._calendar_number], timeout=60)
        pdf_response.raise_for_status()
        collections = _parse_pdf(pdf_response.content)
        if not collections:
            raise ValueError(
                f"No collection dates found in East Hampshire calendar "
                f"{self._calendar_number}. The PDF format may have changed."
            )

        _LOGGER.debug(
            "Found %d collections for East Hampshire calendar %d",
            len(collections),
            self._calendar_number,
        )
        return collections
