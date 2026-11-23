"""
East Lindsey District Council - Waste Collection Schedule
=========================================================

This source retrieves household waste collection dates from East Lindsey
District Council's online waste collection service, using a property's
Unique Property Reference Number (UPRN).

The council provides collection information through two different mechanisms,
requiring separate approaches for standard waste and garden waste.

STANDARD WASTE COLLECTIONS
--------------------------
For refuse, recycling, purple-bin and food-waste collections, the source
queries the council's existing online address lookup service.

The process involves:
    1. Establishing a session with the council's website.
    2. Submitting the property's UPRN through the council's web form.
    3. Decoding the Base64-encoded response containing collection information.
    4. Extracting the next available collection date for each waste type.

These dates are supplied directly by the council as structured information.
The source therefore does not need to calculate or predict collection dates.

GARDEN WASTE COLLECTIONS
------------------------
The council does not expose the complete garden-waste collection schedule as 
structured data through the same lookup service.

Instead, the response identifies the applicable garden-waste calendar using
a PDF identifier, collection weekday and collection week (A or B).

The council publishes annual PDF calendars in which collection dates are
indicated visually by green-highlighted cells. Which is great for humans but 
terrible for machines.

To retrieve the actual collection dates, this source:

    1. Identifies the appropriate garden-waste PDF calendar(s) for the property.
    2. Downloads the current and, where available, previous calendar PDFs.
    3. Uses pdfminer.six to inspect the PDF's text and graphical elements.
    4. Identifies collection dates by locating green-filled rectangles.
    5. Extracts the day numbers printed within those rectangles.
    6. Reconstructs month headings from individual PDF text characters.
    7. Associates each highlighted day with its corresponding month and year.
    8. Validates the resulting dates and removes duplicates.

Importantly, the source reads the actual dates published by the council.
It does NOT assume that garden-waste collections occur every fortnight or some
other interval.

This distinction is particularly important during winter, when collections
typically become less frequent or follow an irregular schedule.

LIMITATIONS AND MAINTENANCE
---------------------------
The garden-waste extraction method is necessary because the council publishes
the schedule primarily as a visual PDF rather than machine-readable data.

Consequently, the parser depends on aspects of the PDF's layout, including
the positioning of month headings, date cells and their highlighting colour.

If the council changes its PDF design, the extraction logic may require
updating. The source attempts to detect parsing failures rather than silently
generating potentially incorrect collection dates.

It would be great if ELDC would publish all collection dates through a structured
API or an iCalendar (.ics) subscription, removing the need for PDF parsing. But I 
think zero chance of that happening - this is ELDC.

DEPENDENCIES
------------
    curl_cffi     - HTTP requests and council website session handling.
    pdfminer.six  - Extraction of text and graphical elements from PDF files.

The resulting collection dates are returned in the format expected by the
Home Assistant Waste Collection Schedule integration.
"""

import base64
import datetime
import io
import json
import logging
import re
from html import unescape

from curl_cffi import requests
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTContainer, LTRect
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "East Lindsey District Council"
DESCRIPTION = "Source for East Lindsey District Council waste collection."
URL = "https://www.e-lindsey.gov.uk"
TEST_CASES = {"13 Firbeck Avenue, Skegness": {"uprn": "100030786099"}}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your UPRN using a tool like findmyaddress.co.uk or finders.io."
}
PARAM_DESCRIPTIONS = {"en": {"uprn": "Unique Property Reference Number (UPRN)"}}
PARAM_TRANSLATIONS = {"en": {"uprn": "UPRN"}}
ICON_MAP = {
    "Refuse": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden Waste": Icons.GARDEN,
    "Purple Bin": Icons.RECYCLING,
    "Food Waste": Icons.GENERAL_WASTE,
}
_PAGE_URL = f"{URL}/mywastecollections"
_ORDINAL_RE = re.compile(r"(\d+)(st|nd|rd|th)\b", re.I)
_LOG = logging.getLogger(__name__)
_GREEN_RGB = (146 / 255, 208 / 255, 80 / 255)
_MONTHS = {name: i for i, name in enumerate((
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
), 1)}

def _parse_date(value: str) -> datetime.date | None:
    if not value:
        return None
    parts = _ORDINAL_RE.sub(r"\1", value).split()
    if len(parts) != 4:
        return None
    try:
        return datetime.datetime.strptime(" ".join(parts[1:]), "%d %B %Y").date()
    except ValueError:
        return None

def _walk(obj):
    yield obj
    if isinstance(obj, LTContainer):
        for child in obj:
            yield from _walk(child)

def _is_green(color):
    return (
        isinstance(color, (tuple, list))
        and len(color) == 3
        and all(abs(float(a) - b) < 0.025 for a, b in zip(color, _GREEN_RGB))
    )

def _extract_month_headings(chars):
    # Recover month names from individually positioned PDF characters.
    rows = {}
    for char in chars:
        if char.get_text().isalpha():
            rows.setdefault(round(char.y0, 1), []).append(char)

    headings = []
    for y, row_chars in rows.items():
        row_chars.sort(key=lambda c: c.x0)
        words, current, previous_end = [], [], None
        for char in row_chars:
            if previous_end is not None and char.x0 - previous_end > 3:
                if current:
                    words.append(current)
                current = []
            current.append(char)
            previous_end = char.x1
        if current:
            words.append(current)
        for word_chars in words:
            word = "".join(c.get_text() for c in word_chars).capitalize()
            if word in _MONTHS:
                headings.append({
                    "month": _MONTHS[word],
                    "name": word,
                    "x": (word_chars[0].x0 + word_chars[-1].x1) / 2,
                    "y": y,
                })
    headings.sort(key=lambda h: (-round(h["y"] / 10), h["x"]))
    return headings

def _extract_day(rect, chars):
    enclosed = [
        c for c in chars
        if c.get_text().isdigit()
        and rect.x0 - 1.5 <= (c.x0 + c.x1) / 2 <= rect.x1 + 1.5
        and rect.y0 - 1.5 <= (c.y0 + c.y1) / 2 <= rect.y1 + 1.5
    ]
    text = "".join(c.get_text() for c in sorted(enclosed, key=lambda c: c.x0))
    return int(text) if text.isdigit() and 1 <= int(text) <= 31 else None

def _pdf_green_dates(pdf_content: bytes, start_year: int,
                     expected_weekday: int | None = None) -> list[datetime.date]:

    # Extract highlighted dates from the council's calendar PDF.
    # Start_year is the year of the first month heading in reading order.

    found = set()
    for page in extract_pages(io.BytesIO(pdf_content)):
        objects = list(_walk(page))
        chars = [obj for obj in objects if isinstance(obj, LTChar)]
        rectangles = [
            obj for obj in objects
            if isinstance(obj, LTRect)
            and _is_green(getattr(obj, "non_stroking_color", None))
        ]
        headings = _extract_month_headings(chars)
        if len(headings) < 12:
            raise ValueError(f"Expected at least 12 month headings; found {len(headings)}")

        year, previous_month = start_year, None
        for heading in headings:
            if previous_month is not None and heading["month"] < previous_month:
                year += 1
            heading["year"] = year
            previous_month = heading["month"]

        calendar_cells = 0
        for rect in rectangles:
            if not (8 <= rect.width <= 40 and 8 <= rect.height <= 35):
                continue
            day = _extract_day(rect, chars)
            if day is None:
                continue  # e.g. green swatch in the legend
            calendar_cells += 1
            cx = (rect.x0 + rect.x1) / 2
            cy = (rect.y0 + rect.y1) / 2
            candidates = []
            for heading in headings:
                dx = abs(cx - heading["x"])
                dy = heading["y"] - cy
                if 0 < dy < 120 and dx < 65:
                    candidates.append((dx ** 2 + dy ** 2, heading))
            if not candidates:
                raise ValueError(f"No month heading for highlighted day {day} at {cx}, {cy}")
            heading = min(candidates, key=lambda item: item[0])[1]
            date = datetime.date(heading["year"], heading["month"], day)
            if expected_weekday is not None and date.weekday() != expected_weekday:
                raise ValueError(f"Unexpected collection weekday: {date}")
            found.add(date)
        if calendar_cells != len(found):
            _LOG.debug("East Lindsey: %d highlighted cells, %d distinct dates",
                       calendar_cells, len(found))
    if not found:
        raise ValueError("No highlighted garden-waste collection dates found")
    return sorted(found)

def _green_pdf_urls(result: dict) -> list[str]:
    urls = []
    for prefix in ("green", "greenold"):
        pdf_id = str(result.get(f"{prefix}pdfid", ""))
        day = str(result.get(f"{prefix}day", ""))
        week = str(result.get(f"{prefix}week", ""))
        if (pdf_id.isdigit() and day in ("Monday", "Tuesday", "Wednesday",
                                         "Thursday", "Friday") and week in ("A", "B")):
            urls.append(f"{URL}/media/{pdf_id}/file/PDF/{day}{week}.pdf")
    return list(dict.fromkeys(urls))

class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome124")
        r = session.get(_PAGE_URL, timeout=30)
        r.raise_for_status()
        html = r.text

        prefix_match = re.search(r'name="([A-Z0-9]+)_PAGESESSIONID"', html)
        if not prefix_match:
            raise SourceArgumentNotFound("uprn", self._uprn, "Could not find form prefix")
        prefix = prefix_match.group(1)
        action_match = re.search(
            r'<form[^>]+action="(https://[^"]+/processsubmission[^"]*)"', html
        )
        if not action_match:
            raise SourceArgumentNotFound("uprn", self._uprn, "Could not find form action")
        submit_url = unescape(action_match.group(1))

        tokens = {}
        for key in ("PAGESESSIONID", "SESSIONID", "NONCE"):
            match = re.search(rf'name="{prefix}_{key}"\s+value="([^"]+)"', html)
            if not match:
                raise SourceArgumentNotFound("uprn", self._uprn, f"Missing {key} token")
            tokens[key] = match.group(1)

        variables = base64.b64encode(json.dumps({
            "ADDRESSSOURCE": {"value": "NLPGEL", "scope": "SERVERCLIENTWITHUPDATE"},
            "ADDRESSUPRN": {"value": self._uprn, "scope": "SERVERCLIENTWITHUPDATE"},
            "TESTDATELAYOUT_DISPLAYED": {"value": False, "scope": "SERVERCLIENT"},
        }).encode()).decode()
        form_data = {
            **{f"{prefix}_{key}": value for key, value in tokens.items()},
            f"{prefix}_VARIABLES": variables,
            f"{prefix}_PAGENAME": "LOOKUP",
            f"{prefix}_PAGEINSTANCE": "0",
            f"{prefix}_LOOKUP_CHOSENADDRESS": self._uprn,
            f"{prefix}_FORMACTION_NEXT": f"{prefix}_LOOKUP_FIELD2",
        }
        r = session.post(submit_url, data=form_data, timeout=30)
        r.raise_for_status()
        match = re.search(rf'{prefix}FormData\s*=\s*"([^"]+)"', r.text)
        if not match:
            raise SourceArgumentNotFound("uprn", self._uprn, "No collection data returned")
        payload = json.loads(base64.b64decode(match.group(1)).decode("utf-8"))
        result_list = payload.get("RESULTS_1", {}).get("FIELD12", {}).get("result", [])
        if not result_list:
            raise SourceArgumentNotFound("uprn", self._uprn, "No collection results found")
        result = result_list[0]

        dates = set()
        for field, waste_type in (
            ("wastenextref", "Refuse"),
            ("wastenextrec", "Recycling"),
            ("wastenextpur", "Purple Bin"),
            ("wastenextfood", "Food Waste"),
        ):
            date = _parse_date(result.get(field, ""))
            if date:
                dates.add((date, waste_type))

        pdf_dates = set()
        first_green_date = _parse_date(result.get("greenfirst", ""))
        
        # Current council calendar begins in March; its first scheduled
        # Collection (greenfirst) is in April of that same calendar year.
        # Previous PDF is the preceding annual calendar.
        
        current_start_year = (
            first_green_date.year if first_green_date else datetime.date.today().year
        )
        for pdf_url in _green_pdf_urls(result):
            is_previous = f"/media/{result.get('greenoldpdfid')}/" in pdf_url
            try:
                response = session.get(pdf_url, timeout=30)
                response.raise_for_status()
                if not response.content.startswith(b"%PDF-"):
                    raise ValueError("Response is not a PDF")
                start_year = current_start_year - int(is_previous)
                expected_day = result.get("greenoldday" if is_previous else "greenday", "")
                weekday = (
                    ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday").index(expected_day)
                    if expected_day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
                    else None
                )
                parsed = _pdf_green_dates(response.content, start_year, weekday)
                pdf_dates.update(parsed)
                _LOG.debug("East Lindsey: %d garden dates from %s", len(parsed), pdf_url)
            except Exception as exc:
                _LOG.warning("East Lindsey: cannot read garden PDF %s: %s", pdf_url, exc)

        if pdf_dates:
            for date in pdf_dates:
                dates.add((date, "Garden Waste"))
        else:
            # This date can be in the past: never extrapolate a false schedule.
            fallback = first_green_date
            if fallback:
                dates.add((fallback, "Garden Waste"))
            _LOG.warning("East Lindsey: using single garden-waste fallback date")

        return [Collection(date=date, t=kind, icon=ICON_MAP[kind])
                for date, kind in sorted(dates, key=lambda x: (x[0], x[1]))]
