"""Waste collection schedules for East Hampshire District Council.

The council publishes one PDF calendar per round (and one per garden-waste
round). The collection type is not printed: each date cell is filled with a
colour (green rubbish, grey recycling, blue glass, pale blue garden waste), so
``PdfLayoutParser`` exposes the positioned dates and the filled rectangles and
``_calendar_rows`` pairs them up.

The calendars are found either through the property's UPRN (the council's map
service names the property's own calendars) or by the calendar number printed
on the council's index page.
"""

import logging
import re
from collections.abc import Iterable
from datetime import date
from typing import Any, ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, integer, uprn
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import Compose, Deduplicate, SortRows
from waste_collection_schedule.transformers import ICSTransformer

_LOGGER = logging.getLogger(__name__)

_URL = "https://www.easthants.gov.uk"
_SCHEDULE_URL = f"{_URL}/bin-collections/find-your-bin-calendar"
_ADDRESS_URL = "https://maps.easthants.gov.uk/easthampshire.aspx"

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
_COLOURS: dict[str, tuple[tuple[float, ...], ...]] = {
    "rubbish": ((0.248, 0.646, 0.209),),
    "recycling": ((0.391, 0.389, 0.387), (0.438, 0.437, 0.434)),
    "glass": ((0.0, 0.46, 0.748),),
    "garden": ((0.6, 0.71, 1.0, 0.3),),
    "suspended": ((0.31, 0.98, 0.0, 0.0),),
}
_COLOUR_TOLERANCE = 0.02

# The shared vocabulary resolves "Rubbish", "Recycling", "Glass" and
# "Garden waste"; they are listed to keep the mapping explicit.
_TYPE_MAP = {
    "Rubbish": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Glass": wt.GLASS,
    "Garden waste": wt.GARDEN_WASTE,
}
_TYPE_LABELS = {
    "rubbish": "Rubbish",
    "recycling": "Recycling",
    "glass": "Glass",
    "garden": "Garden waste",
}


def _colour_matches(
    actual: tuple[float, ...] | None, expected: tuple[float, ...]
) -> bool:
    if actual is not None and len(actual) == 1 and len(expected) == 3:
        actual = (actual[0],) * 3  # greyscale fill
    return bool(
        actual
        and len(actual) == len(expected)
        and all(
            abs(actual[index] - expected[index]) <= _COLOUR_TOLERANCE
            for index in range(len(expected))
        )
    )


def _calendar_links(html: str) -> tuple[dict[int, str], dict[int, str]]:
    """Return the bin and garden calendar links of the council's index page."""
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


def _uprn_calendar_urls(html: str, uprn_value: str) -> dict[str, str]:
    """Read the property's own calendar links off the council's map page."""
    soup = BeautifulSoup(html, "html.parser")
    panel = soup.find(
        "div", attrs={"aria-label": re.compile("waste and recycling", re.IGNORECASE)}
    )
    if panel is None:
        raise SourceArgumentNotFound(
            "uprn", uprn_value, "no East Hampshire address was found."
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
            uprn_value,
            "the council did not provide a bin calendar for this property.",
        )
    return urls


def _calendar_number(argument: str, value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceArgumentNotFound(argument, value) from exc
    if number < 1:
        raise SourceArgumentNotFound(argument, value)
    return number


def _uprn_pick(response, *_, uprn: Any = None, **__) -> list[str]:
    """Lookup pick: the bin (and garden) calendar URLs assigned to the UPRN."""
    value = str(uprn).strip()
    if not value.isdigit():
        raise SourceArgumentNotFound("uprn", uprn)
    urls = _uprn_calendar_urls(response.text, value)
    return [urls["bins"], *([urls["garden"]] if "garden" in urls else [])]


def _manual_pick(
    response,
    *_,
    calendar_number: Any = None,
    garden_calendar_number: Any = None,
    **__,
) -> list[str]:
    """Lookup pick: the calendar URLs for the numbers printed on the index page."""
    links, garden_links = _calendar_links(response.text)
    number = _calendar_number("calendar_number", calendar_number)
    if number not in links:
        raise SourceArgumentNotFoundWithSuggestions(
            "calendar_number", number, sorted(links)
        )
    urls = [links[number]]
    if garden_calendar_number not in (None, ""):
        garden = _calendar_number("garden_calendar_number", garden_calendar_number)
        if garden not in garden_links:
            raise SourceArgumentNotFoundWithSuggestions(
                "garden_calendar_number", garden, sorted(garden_links)
            )
        urls.append(garden_links[garden])
    return urls


def _has_uprn(*_, uprn: Any = None, **__) -> bool:
    return uprn not in (None, "")


def _has_no_uprn(*_, uprn: Any = None, **__) -> bool:
    return uprn in (None, "")


def _collection_type(
    rectangles: list[tuple[float, float, float, float, str]],
    text_x: float,
    text_y: float,
) -> str | None:
    # Each calendar column is roughly 83pt wide. Looking no more than 70pt to
    # the right includes the bank-holiday icon cell without reaching the next
    # calendar column.
    for x0, y0, x1, y1, type_key in rectangles:
        if y0 - 1 <= text_y <= y1 + 1 and x1 >= text_x - 5 and x0 <= text_x + 70:
            return type_key
    return None


def _rectangles(
    vectors: Iterable[parsers.PdfVector], page: int
) -> list[tuple[float, float, float, float, str]]:
    """The collection-coloured date cells of one page as (x0, y0, x1, y1, type)."""
    found = []
    for vector in vectors:
        if vector.page != page:
            continue
        # Date cells are 53-71pt wide. On bank-holiday rows the date part is
        # orange, but the adjacent 16-17pt icon cell retains the collection
        # colour. Ignore smaller icon artwork and large legends.
        width = vector.x1 - vector.x0
        height = vector.y1 - vector.y0
        if not (10 <= width <= 75 and 10 <= height <= 16):
            continue
        for type_key, colours in _COLOURS.items():
            if any(_colour_matches(vector.fill_color, colour) for colour in colours):
                found.append((vector.x0, vector.y0, vector.x1, vector.y1, type_key))
                break
    return found


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


def _calendar_rows(
    layout: parsers.PdfDocumentLayout, source: BaseSource | None = None
) -> Iterable[tuple[date, str]]:
    """Pair every printed date of one PDF with the colour of its cell."""
    source_name = response_shape.source_name(source)
    unmatched: list[str] = []
    found = 0
    for page in sorted({fragment.page for fragment in layout.fragments}):
        rectangles = _rectangles(layout.vectors, page)
        separate_glass = any(item[4] == "glass" for item in rectangles)
        month_by_column: dict[float, tuple[int, int]] = {}

        for fragment in layout.fragments:
            if fragment.page != page:
                continue
            text = fragment.text.upper()
            column = round(fragment.x, 1)
            if month_match := _MONTH_RE.fullmatch(text):
                month = _MONTHS[month_match.group(1)]
                month_by_column[column] = (
                    _normalise_heading_year(
                        int(month_match.group(2)), month, month_by_column.get(column)
                    ),
                    month,
                )
                continue

            date_match = _DATE_RE.fullmatch(text)
            if not date_match or column not in month_by_column:
                continue

            year, month = month_by_column[column]
            collection_date = date(year, month, int(date_match.group(1)))
            type_key = _collection_type(rectangles, fragment.x, fragment.y)
            if type_key is None:
                unmatched.append(collection_date.isoformat())
                continue
            if type_key == "suspended":
                continue

            found += 1
            yield collection_date, _TYPE_LABELS[type_key]
            if type_key == "recycling" and not separate_glass:
                # Without a glass colour the recycling day includes glass.
                yield collection_date, "Glass"

    response_shape.expect(
        not unmatched,
        source_name=source_name,
        detail="could not determine collection types for PDF dates: "
        + ", ".join(unmatched),
        raw=layout.text[:500],
    )
    response_shape.expect(
        found > 0,
        source_name=source_name,
        detail="no collection dates found in the calendar PDF",
        raw=layout.text[:500],
    )


@final
class Source(BaseSource):
    TITLE = "East Hampshire District Council"
    DESCRIPTION = "Waste collection schedules for East Hampshire District Council."
    URL = _URL
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@alexcroox"]

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
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

    PARAMS = (
        alternatives([uprn()], [integer("calendar_number", "Calendar number")]),
        integer("garden_calendar_number", "Garden waste calendar number"),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Open https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar. "
            "Use the map near the bottom of the page to find your address and its "
            "Unique Property Ref, then enter that as the UPRN; the council then "
            "supplies your bin and garden calendars itself. Alternatively, enter "
            "the calendar number shown on that page (for example 16 for "
            "'Calendar 16') and, if you have a garden waste subscription, the "
            "numeric part of your garden calendar (for example 1 for 'G1')."
        )
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(
                _ADDRESS_URL,
                params=lambda *_, uprn=None, **__: {
                    "action": "SetAddress",
                    "UniqueId": str(uprn).strip(),
                },
                when=_has_uprn,
                pick=_uprn_pick,
                timeout=30,
            ),
            retrievers.Lookup(
                _SCHEDULE_URL,
                when=_has_no_uprn,
                pick=_manual_pick,
                timeout=30,
            ),
        ),
        targets=lambda source, urls: [url for found in urls if found for url in found],
        fetch=retrievers.Request(lambda url, *_, **__: url, timeout=60),
    )
    parse = parsers.EachResponse(
        parsers.PdfLayoutParser(min_fragments=20, min_vectors=20),
        then=_calendar_rows,
    )
    preprocess = Compose(Deduplicate(), SortRows())
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
