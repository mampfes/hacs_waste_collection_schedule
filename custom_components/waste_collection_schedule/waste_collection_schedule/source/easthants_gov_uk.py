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
    SourceArgumentRequired,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "East Hampshire District Council"
DESCRIPTION = "Waste collection schedules for East Hampshire District Council."
URL = "https://www.easthants.gov.uk"
COUNTRY = "uk"
SOURCE_CODEOWNERS = ["@alexcroox"]

_SCHEDULE_URL = f"{URL}/bin-collections/find-your-bin-calendar"
_ADDRESS_URL = "https://maps.easthants.gov.uk/easthampshire.aspx"
_HEADERS = {"User-Agent": "waste-collection-schedule/easthants_gov_uk"}
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
_GARDEN_CALENDAR_LINK_RE = re.compile(r"^G(\d+)\b", re.IGNORECASE)

# Fill colours used for collection rows in the council PDFs. The main bin
# calendars use RGB, while the garden calendars use CMYK.
_RUBBISH_COLOUR = (0.248, 0.646, 0.209)
_RECYCLING_COLOUR = (0.391, 0.389, 0.387)
_HARD_TO_REACH_RECYCLING_COLOUR = (0.438, 0.437, 0.434)
_GLASS_COLOUR = (0.0, 0.46, 0.748)
_GARDEN_COLOUR = (0.6, 0.71, 1.0, 0.3)
_SUSPENDED_COLOUR = (0.31, 0.98, 0.0, 0.0)
_COLOUR_TOLERANCE = 0.02

_TYPE_MAP = {
    "rubbish": ("Rubbish",),
    "recycling": ("Recycling",),
    "glass": ("Glass",),
    "garden": ("Garden waste",),
}
ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Glass": Icons.GLASS,
    "Garden waste": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": (
            "The property's Unique Property Reference Number (UPRN). When set, "
            "the council automatically supplies its bin and garden calendars."
        ),
        "calendar_number": (
            "Optional manual bin calendar number, used when no UPRN is provided."
        ),
        "garden_calendar_number": (
            "Optional manual garden waste calendar number (the numeric part of "
            "G1-G10), used when no UPRN is provided."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "calendar_number": "Calendar number",
        "garden_calendar_number": "Garden waste calendar number",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar. "
        "Use the map near the bottom of the page to find your address and its "
        "Unique Property Ref, then enter that as the UPRN. Alternatively, enter "
        "the displayed calendar numbers manually."
    ),
}

TEST_CASES = {
    "UPRN lookup": {"uprn": 1710041123},
    "Calendar 16 with garden waste G1": {
        "calendar_number": 16,
        "garden_calendar_number": 1,
    },
    "Calendar 1 without garden waste": {
        "calendar_number": 1,
    },
    "Calendar 20 with garden waste G10": {
        "calendar_number": 20,
        "garden_calendar_number": 10,
    },
}


def _colour_matches(
    actual: tuple[float, ...] | None, expected: tuple[float, ...]
) -> bool:
    return bool(
        actual
        and len(actual) == len(expected)
        and all(
            abs(actual[index] - expected[index]) <= _COLOUR_TOLERANCE
            for index in range(len(expected))
        )
    )


def _calendar_links(html: str) -> tuple[dict[int, str], dict[int, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links: dict[int, str] = {}
    garden_links: dict[int, str] = {}

    for anchor in soup.find_all("a", href=True):
        label = " ".join(anchor.stripped_strings)
        match = _CALENDAR_LINK_RE.match(label)
        if match:
            links[int(match.group(1))] = urljoin(_SCHEDULE_URL, str(anchor["href"]))
            continue

        garden_match = _GARDEN_CALENDAR_LINK_RE.match(label)
        if garden_match:
            garden_links[int(garden_match.group(1))] = urljoin(
                _SCHEDULE_URL, str(anchor["href"])
            )

    return links, garden_links


def _secure_calendar_url(href: str) -> str:
    url = urljoin(_ADDRESS_URL, href)
    if url.startswith("http://maps.easthants.gov.uk/"):
        return "https://" + url.removeprefix("http://")
    return url


def _uprn_calendar_urls(html: str, uprn: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    panel = soup.find(
        "div", attrs={"aria-label": re.compile("waste and recycling", re.IGNORECASE)}
    )
    if panel is None:
        raise SourceArgumentNotFound(
            "uprn", uprn, "no East Hampshire address was found."
        )

    urls: dict[str, str] = {}
    for heading in panel.find_all("h4"):
        section = heading.find_parent("div", class_="atPanelContent")
        if section is None or (link := section.find("a", href=True)) is None:
            continue

        title = heading.get_text(" ", strip=True).casefold()
        if "garden" in title:
            urls["garden"] = _secure_calendar_url(str(link["href"]))
        elif "bin calendar" in title:
            urls["bins"] = _secure_calendar_url(str(link["href"]))

    if "bins" not in urls:
        raise SourceArgumentNotFound(
            "uprn",
            uprn,
            "the council did not provide a bin calendar for this property.",
        )
    return urls


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
        elif operator == b"k" and len(operands) >= 4:
            try:
                fill_colour = tuple(float(value) for value in operands[:4])
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
            elif _colour_matches(fill_colour, _RECYCLING_COLOUR) or _colour_matches(
                fill_colour, _HARD_TO_REACH_RECYCLING_COLOUR
            ):
                type_key = "recycling"
            elif _colour_matches(fill_colour, _GLASS_COLOUR):
                type_key = "glass"
            elif _colour_matches(fill_colour, _GARDEN_COLOUR):
                type_key = "garden"
            elif _colour_matches(fill_colour, _SUSPENDED_COLOUR):
                type_key = "suspended"
            else:
                continue

            try:
                x, y, width, height = (float(value) for value in operands)
            except (TypeError, ValueError):
                continue

            # Date cells are 53-71pt wide. On bank-holiday rows the date part is
            # orange, but the adjacent 16-17pt icon cell retains the collection
            # colour. Ignore smaller icon artwork and large legends.
            if not (10 <= abs(width) <= 75 and 10 <= abs(height) <= 16):
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


def _waste_types(type_key: str, separate_glass: bool) -> tuple[str, ...]:
    if type_key == "recycling" and not separate_glass:
        return (*_TYPE_MAP[type_key], "Glass")
    return _TYPE_MAP[type_key]


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
    separate_glass = any(type_key == "glass" for *_, type_key in rectangles)
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
        if type_key == "suspended":
            continue

        collections.extend(
            Collection(collection_date, waste_type, icon=ICON_MAP[waste_type])
            for waste_type in _waste_types(type_key, separate_glass)
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


def _validate_calendar_number(argument: str, value: int) -> int:
    try:
        calendar_number = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceArgumentNotFound(argument, value) from exc

    if calendar_number < 1:
        raise SourceArgumentNotFound(argument, value)
    return calendar_number


def _validate_uprn(value: str | int) -> str:
    uprn = str(value).strip()
    if not uprn.isdigit():
        raise SourceArgumentNotFound("uprn", value)
    return uprn


class Source:
    def __init__(
        self,
        uprn: str | int | None = None,
        calendar_number: int | None = None,
        garden_calendar_number: int | None = None,
    ):
        self._uprn = None if uprn is None else _validate_uprn(uprn)
        self._calendar_number = (
            None
            if calendar_number is None
            else _validate_calendar_number("calendar_number", calendar_number)
        )
        self._garden_calendar_number = (
            None
            if garden_calendar_number is None
            else _validate_calendar_number(
                "garden_calendar_number", garden_calendar_number
            )
        )
        if self._uprn is None and self._calendar_number is None:
            raise SourceArgumentRequired(
                "uprn", "provide a UPRN or a manual calendar number."
            )

    @staticmethod
    def _fetch_calendar(
        session: requests.Session, url: str, calendar_name: str
    ) -> list[Collection]:
        pdf_response = session.get(url, timeout=60)
        pdf_response.raise_for_status()
        collections = _parse_pdf(pdf_response.content)
        if not collections:
            raise ValueError(
                f"No collection dates found in East Hampshire calendar "
                f"{calendar_name}. The PDF format may have changed."
            )
        return collections

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(_HEADERS)

        if self._uprn is not None:
            address_response = session.get(
                _ADDRESS_URL,
                params={"action": "SetAddress", "UniqueId": self._uprn},
                timeout=30,
            )
            address_response.raise_for_status()
            urls = _uprn_calendar_urls(address_response.text, self._uprn)
            collections = self._fetch_calendar(
                session, urls["bins"], f"for UPRN {self._uprn}"
            )
            if "garden" in urls:
                collections.extend(
                    self._fetch_calendar(
                        session, urls["garden"], f"garden for UPRN {self._uprn}"
                    )
                )
            source_name = f"UPRN {self._uprn}"
        else:
            page_response = session.get(_SCHEDULE_URL, timeout=30)
            page_response.raise_for_status()

            links, garden_links = _calendar_links(page_response.text)
            if self._calendar_number not in links:
                raise SourceArgumentNotFoundWithSuggestions(
                    "calendar_number", self._calendar_number, sorted(links)
                )

            collections = self._fetch_calendar(
                session, links[self._calendar_number], str(self._calendar_number)
            )

            if self._garden_calendar_number is not None:
                if self._garden_calendar_number not in garden_links:
                    raise SourceArgumentNotFoundWithSuggestions(
                        "garden_calendar_number",
                        self._garden_calendar_number,
                        sorted(garden_links),
                    )
                collections.extend(
                    self._fetch_calendar(
                        session,
                        garden_links[self._garden_calendar_number],
                        f"G{self._garden_calendar_number}",
                    )
                )
            source_name = f"calendar {self._calendar_number}"

        collections.sort(key=lambda item: (item.date, item.type))
        _LOGGER.debug(
            "Found %d collections for East Hampshire %s",
            len(collections),
            source_name,
        )
        return collections
