from __future__ import annotations

import datetime
import json
import logging
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from io import BytesIO
from statistics import median
from typing import Any

from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTChar,
    LTLayoutContainer,
    LTRect,
    LTTextLine,
)
from pypdf import PdfReader
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Hornsby Shire Council"
DESCRIPTION = "Source for Hornsby Shire Council."
URL = "https://hornsby.nsw.gov.au/"
TEST_CASES = {
    "1 Cherrybrook Road, West Pennant Hills, 2125": {
        "address": "1 Cherrybrook Road, West Pennant Hills, 2125"
    },
    "10 Albion Street, Pennant Hills, 2120": {
        "address": "10 Albion Street, Pennant Hills, 2120"
    },
}

ICON_MAP = {
    "Green Waste": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "General Waste": "mdi:trash-can",
    "Bulky Waste": "mdi:delete",
}

MONTH_NUM_MAP = {
    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12,
}

WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

BASE_URL = "https://www.hornsby.nsw.gov.au/"

_LOGGER = logging.getLogger(__name__)

# Number of fortnightly occurrences to generate from an anchor date
_FORTNIGHTLY_COUNT = 26
# Number of weekly occurrences to generate from today
_WEEKLY_COUNT = 26


def _http_get(url: str, timeout_s: float = 25.0) -> bytes:
    """Perform an HTTP GET request and return the response body."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ),
            "Accept": "application/json, */*",
            "Referer": "https://www.hornsby.nsw.gov.au/",
            "X-Requested-With": "XMLHttpRequest",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()


def _parse_geolocation_id(response_bytes: bytes) -> str:
    """Parse the Hornsby address search response and return the best matching Id."""
    try:
        data = json.loads(response_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Address search response was not parseable: {e}") from e

    items = data.get("Items", [])
    if not items:
        raise ValueError("No address results returned.")

    items.sort(key=lambda r: r.get("Score", 0), reverse=True)
    return items[0]["Id"]


# ---------------------------------------------------------------------------
# HTML parsing of the waste-services widget
# ---------------------------------------------------------------------------

_DATE_DMY = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_DATE_WDMY = re.compile(
    r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\d{1,2})/(\d{1,2})/(\d{4})"
)
_WEEKDAY_RE = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.IGNORECASE,
)


def _parse_date_text(text: str) -> datetime.date | None:
    """Try to parse a date from a next-service text like 'Wed 8/4/2026' or '26/01/2026'."""
    m = _DATE_WDMY.search(text)
    if not m:
        m = _DATE_DMY.search(text)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def _parse_weekday(text: str) -> int | None:
    """Extract a weekday index (0=Mon) from text like 'Wednesday' or 'Monday/Thursday'."""
    m = _WEEKDAY_RE.search(text)
    if m:
        return WEEKDAY_MAP.get(m.group(1).lower())
    return None


def _next_weekday(weekday: int, from_date: datetime.date) -> datetime.date:
    """Return the next occurrence of the given weekday on or after from_date."""
    days_ahead = (weekday - from_date.weekday()) % 7
    return from_date + datetime.timedelta(days=days_ahead)


def _generate_weekly(weekday: int, count: int = _WEEKLY_COUNT) -> list[datetime.date]:
    """Generate weekly dates starting from the next occurrence of weekday."""
    start = _next_weekday(weekday, datetime.date.today())
    return [start + datetime.timedelta(weeks=i) for i in range(count)]


def _generate_fortnightly(
    anchor: datetime.date, count: int = _FORTNIGHTLY_COUNT
) -> list[datetime.date]:
    """Generate fortnightly dates starting from anchor."""
    return [anchor + datetime.timedelta(weeks=2 * i) for i in range(count)]


class _WasteServiceParser(HTMLParser):
    """Parse the waste-services HTML widget to extract service info."""

    def __init__(self) -> None:
        super().__init__()
        self.services: list[dict[str, str]] = []
        self.hrefs: list[str] = []
        self._in_result = False
        self._current: dict[str, str] = {}
        self._capture_field: str | None = None
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k.lower(): v or "" for k, v in attrs}
        cls = attr_dict.get("class", "")

        if tag == "a" and attr_dict.get("href"):
            self.hrefs.append(attr_dict["href"])

        if tag == "div" and "waste-services-result" in cls:
            self._in_result = True
            self._current = {"classes": cls}
            self._depth = 0

        if self._in_result:
            if tag == "div":
                self._depth += 1
            if tag == "h3":
                self._capture_field = "type"
            elif tag == "div" and "next-service" in cls:
                self._capture_field = "next_service"
            elif tag == "div" and "note" in cls:
                self._capture_field = "note"

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h3", "div") and self._capture_field:
            self._capture_field = None
        if self._in_result and tag == "div":
            self._depth -= 1
            if self._depth <= 0:
                self._in_result = False
                if self._current.get("type"):
                    self.services.append(self._current)
                self._current = {}

    def handle_data(self, data: str) -> None:
        if self._capture_field and self._in_result:
            self._current[self._capture_field] = (
                self._current.get(self._capture_field, "") + data
            )


def _extract_entries_from_html(html: str) -> list[Collection]:
    """Extract collection entries from the waste-services HTML widget."""
    parser = _WasteServiceParser()
    parser.feed(html)

    entries: list[Collection] = []
    seen: set[tuple[datetime.date, str]] = set()
    today = datetime.date.today()

    for svc in parser.services:
        raw_type = svc.get("type", "").strip()
        next_text = svc.get("next_service", "").strip()
        note = svc.get("note", "").strip().lower()

        # Skip calendar-link and non-service entries
        if "calendar" in raw_type.lower() or not next_text:
            continue

        # Determine waste type
        waste_type = raw_type
        if "garbage" in raw_type.lower() or "general" in raw_type.lower():
            waste_type = "General Waste"
        elif "recycling" in raw_type.lower():
            waste_type = "Recycling"
        elif "green" in raw_type.lower():
            waste_type = "Green Waste"
        elif "bulky" in raw_type.lower():
            waste_type = "Bulky Waste"

        # Try to parse a specific date
        specific_date = _parse_date_text(next_text)

        if specific_date:
            if "fortnightly" in note or "fortnight" in note:
                dates = _generate_fortnightly(specific_date)
            else:
                dates = [specific_date]
        else:
            # No specific date — try weekday
            weekday = _parse_weekday(next_text)
            if weekday is not None:
                if "fortnightly" in note or "fortnight" in note:
                    anchor = _next_weekday(weekday, today)
                    dates = _generate_fortnightly(anchor)
                else:
                    dates = _generate_weekly(weekday)
            else:
                continue

        for dt in dates:
            if dt < today:
                continue
            if (dt, waste_type) not in seen:
                seen.add((dt, waste_type))
                entries.append(
                    Collection(date=dt, t=waste_type, icon=ICON_MAP.get(waste_type))
                )

    return entries


# ---------------------------------------------------------------------------
# PDF URL selection
# ---------------------------------------------------------------------------


def _select_weekly_waste_calendar_pdf_href(hrefs: list[str]) -> str | None:
    """Select the weekly waste calendar PDF URL from the list of hrefs."""
    pdfs = [h for h in hrefs if h.lower().endswith(".pdf")]
    if not pdfs:
        return None

    # Weekly waste calendar under 'suds-waste-and-recycling' or 'muds-'
    for pattern in ("suds-waste-and-recycling", "muds-green-waste"):
        cand = [h for h in pdfs if "collection-calendars" in h and pattern in h]
        if cand:
            return cand[0]

    # Fallback: any collection-calendars PDF that doesn't look like bulky-waste
    cand = [h for h in pdfs if "collection-calendars" in h and "bulky" not in h.lower()]
    if cand:
        return cand[0]

    return pdfs[0]


def _select_bulky_waste_calendar_pdf_href(hrefs: list[str]) -> str | None:
    """Select the bulky waste calendar PDF URL from the list of hrefs."""
    pdfs = [h for h in hrefs if h.lower().endswith(".pdf")]
    if not pdfs:
        return None

    preferred = [
        h
        for h in pdfs
        if ("suds-bulky-waste" in h.lower())
        or ("muds-bulky-waste" in h.lower())
        or ("bulkywasteflyer" in h.lower())
        or ("bulkywaste" in h.lower())
    ]
    if preferred:
        return preferred[0]

    cand = [h for h in pdfs if "bulky" in h.lower()]
    if cand:
        return cand[0]

    return None


def _fetch_waste_services_html(address: str, language: str = "en-AU") -> str:
    """Fetch the waste-services HTML widget for a given address."""
    keywords = urllib.parse.quote(address, safe="")
    search_url = f"{BASE_URL}api/v1/myarea/search?keywords={keywords}"

    response_bytes = _http_get(search_url)
    geolocation_id = _parse_geolocation_id(response_bytes)

    waste_services_url = (
        f"{BASE_URL}ocapi/Public/myarea/wasteservices"
        f"?geolocationid={urllib.parse.quote(geolocation_id)}"
        f"&ocsvclang={urllib.parse.quote(language)}"
    )

    ws_json = json.loads(
        _http_get(waste_services_url).decode("utf-8", errors="replace")
    )
    if not ws_json.get("success", False):
        raise ValueError("wasteservices call returned success=false.")

    return ws_json.get("responseContent") or ""


# ---------------------------------------------------------------------------
# PDF extraction (kept as fallback for weekly calendar)
# ---------------------------------------------------------------------------


def _is_near_white(rgb: tuple[float, float, float]) -> bool:
    r, g, b = rgb
    return r > 0.95 and g > 0.95 and b > 0.95


def _classify_fill(rgb: tuple[float, float, float]) -> str:
    r, g, b = rgb
    if g > 0.45 and r < 0.45 and b < 0.45:
        return "green"
    if r > 0.70 and g > 0.55 and b < 0.45:
        return "yellow"
    return "unknown"


def _normalize_color_to_rgb(
    color: Any,
) -> tuple[float, float, float] | None:
    if color is None:
        return None
    if isinstance(color, (list, tuple)):
        if len(color) == 3:
            return (float(color[0]), float(color[1]), float(color[2]))
        if len(color) == 4:
            c, m, y, k = (float(v) for v in color)
            return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
        if len(color) == 1:
            g = float(color[0])
            return (g, g, g)
    if isinstance(color, (int, float)):
        g = float(color)
        return (g, g, g)
    return None


def _iter_layout_elements(container: Any) -> Any:
    for element in container:
        yield element
        if isinstance(element, LTLayoutContainer):
            yield from _iter_layout_elements(element)


def _flush_word(word_chars: list[LTChar], page_height: float) -> dict[str, Any]:
    word_text = "".join(c.get_text() for c in word_chars)
    bx0 = min(c.bbox[0] for c in word_chars)
    by0 = min(c.bbox[1] for c in word_chars)
    bx1 = max(c.bbox[2] for c in word_chars)
    by1 = max(c.bbox[3] for c in word_chars)
    return {
        "text": word_text,
        "x0": bx0,
        "x1": bx1,
        "top": page_height - by1,
        "bottom": page_height - by0,
    }


def _extract_words_from_page(
    page_layout: Any, page_height: float
) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    for element in _iter_layout_elements(page_layout):
        if not isinstance(element, LTTextLine):
            continue
        word_chars: list[LTChar] = []
        for char in element:
            if isinstance(char, LTChar) and char.get_text().strip():
                word_chars.append(char)
            else:
                if word_chars:
                    words.append(_flush_word(word_chars, page_height))
                    word_chars = []
        if word_chars:
            words.append(_flush_word(word_chars, page_height))
    return words


def _group_words_into_lines(
    words: list[dict[str, Any]], y_tolerance: float = 5.0
) -> list[list[dict[str, Any]]]:
    if not words:
        return []
    sorted_words = sorted(words, key=lambda w: float(w["top"]))
    lines: list[list[dict[str, Any]]] = []
    current_line: list[dict[str, Any]] = [sorted_words[0]]
    current_top = float(sorted_words[0]["top"])
    for w in sorted_words[1:]:
        w_top = float(w["top"])
        if w_top - current_top <= y_tolerance:
            current_line.append(w)
        else:
            lines.append(sorted(current_line, key=lambda w: float(w["x0"])))
            current_line = [w]
            current_top = w_top
    if current_line:
        lines.append(sorted(current_line, key=lambda w: float(w["x0"])))
    return lines


def _extract_events_from_weekly_pdf(pdf_bytes: bytes) -> list[Collection]:
    """Extract green waste and recycling events from the weekly calendar PDF."""
    pages = list(extract_pages(BytesIO(pdf_bytes)))
    if not pages:
        raise ValueError("Weekly calendar PDF contains no pages")

    rx = re.compile(
        r"^(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|"
        r"OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})$",
        re.IGNORECASE,
    )

    all_words: list[dict[str, Any]] = []
    all_rects: list[tuple[str, dict[str, Any]]] = []

    for page in pages:
        page_height = float(page.height)
        words = _extract_words_from_page(page, page_height)
        all_words.extend(words)

        for element in _iter_layout_elements(page):
            if not isinstance(element, LTRect):
                continue
            rgb = _normalize_color_to_rgb(element.non_stroking_color)
            if rgb is None or _is_near_white(rgb):
                continue
            bx0, by0, bx1, by1 = element.bbox
            top_coord = page_height - by1
            bottom_coord = page_height - by0
            rect_w = bx1 - bx0
            rect_h = by1 - by0
            if not (10.0 < rect_w < 25.0 and 10.0 < rect_h < 25.0):
                continue
            label = _classify_fill(rgb)
            if label != "unknown":
                all_rects.append(
                    (
                        label,
                        {
                            "x0": bx0,
                            "x1": bx1,
                            "top": top_coord,
                            "bottom": bottom_coord,
                        },
                    )
                )

    text_lines = _group_words_into_lines(all_words)
    headers: list[dict[str, Any]] = []

    for line_words in text_lines:
        line_text = " ".join(w["text"] for w in line_words).strip()
        m = rx.match(line_text)
        if not m:
            continue

        x0 = min(float(w["x0"]) for w in line_words)
        x1 = max(float(w["x1"]) for w in line_words)
        top = min(float(w["top"]) for w in line_words)
        bottom = max(float(w["bottom"]) for w in line_words)
        cx = (x0 + x1) / 2.0
        cy = (top + bottom) / 2.0
        headers.append(
            {
                "month": m.group(1).upper(),
                "year": int(m.group(2)),
                "center": (cx, cy),
                "col": None,
            }
        )

    if not headers:
        raise ValueError("No month headers found in weekly calendar PDF.")

    # Assign columns to headers using k-means-like clustering
    ncols = 4
    xs = [h["center"][0] for h in headers]
    xs_sorted = sorted(xs)
    n = len(xs_sorted)
    centers = [
        xs_sorted[min(int(q * (n - 1) + 0.5), n - 1)]
        for q in (0.1 + i * 0.8 / (ncols - 1) for i in range(ncols))
    ]

    for _ in range(10):
        assignments = [min(range(ncols), key=lambda c: abs(x - centers[c])) for x in xs]
        new_centers = list(centers)
        for c in range(ncols):
            members = [xs[i] for i in range(len(xs)) if assignments[i] == c]
            if members:
                new_centers[c] = sum(members) / len(members)
        if all(abs(new_centers[c] - centers[c]) < 0.5 for c in range(ncols)):
            centers = new_centers
            break
        centers = new_centers

    col_centers = sorted(centers)

    for h in headers:
        h["col"] = min(
            range(len(col_centers)),
            key=lambda i: abs(h["center"][0] - col_centers[i]),
        )

    digit_words: list[tuple[int, dict[str, Any]]] = [
        (int(w["text"]), w) for w in all_words if re.fullmatch(r"\d{1,2}", w["text"])
    ]

    by_fill: dict[str, list[dict[str, Any]]] = {}
    for label, rect in all_rects:
        by_fill.setdefault(label, []).append(rect)

    marker_sets: dict[str, list[dict[str, Any]]] = {}
    for label, items in by_fill.items():
        item_widths = [float(it["x1"]) - float(it["x0"]) for it in items]
        item_heights = [float(it["bottom"]) - float(it["top"]) for it in items]
        med_w = median(item_widths)
        med_h = median(item_heights)

        keep = [
            it
            for it, w, h in zip(items, item_widths, item_heights)
            if abs(w - med_w) < 2.0 and abs(h - med_h) < 2.0
        ]
        if len(keep) >= 10:
            marker_sets[label] = keep

    if not {"green", "yellow"}.issubset(marker_sets):
        raise ValueError(
            f"Could not detect both marker sets. Detected={list(marker_sets)}"
        )

    entries: list[Collection] = []
    seen: set[tuple[datetime.date, str]] = set()

    for color, markers in marker_sets.items():
        waste_type = "Green Waste" if color == "green" else "Recycling"

        for marker in markers:
            m_x0 = float(marker["x0"])
            m_top = float(marker["top"])
            m_x1 = float(marker["x1"])
            m_bottom = float(marker["bottom"])
            cx = (m_x0 + m_x1) / 2.0
            cy = (m_top + m_bottom) / 2.0

            day = None
            for digit, wrect in digit_words:
                w_x0 = float(wrect["x0"])
                w_top = float(wrect["top"])
                w_x1 = float(wrect["x1"])
                w_bottom = float(wrect["bottom"])
                if w_x0 <= cx <= w_x1 and w_top <= cy <= w_bottom:
                    day = digit
                    break
            if day is None:
                best_score = -1.0
                for digit, wrect in digit_words:
                    w_x0 = float(wrect["x0"])
                    w_top = float(wrect["top"])
                    w_x1 = float(wrect["x1"])
                    w_bottom = float(wrect["bottom"])
                    ix0 = max(m_x0, w_x0)
                    iy0 = max(m_top, w_top)
                    ix1 = min(m_x1, w_x1)
                    iy1 = min(m_bottom, w_bottom)
                    if ix0 < ix1 and iy0 < iy1:
                        score = (ix1 - ix0) * (iy1 - iy0)
                        if score > best_score:
                            best_score = score
                            day = digit
            if day is None:
                continue

            col = min(
                range(len(col_centers)),
                key=lambda i: abs(cx - col_centers[i]),
            )
            candidates = [
                h for h in headers if h["col"] == col and h["center"][1] <= cy + 1.0
            ]
            if candidates:
                mh = max(candidates, key=lambda h: h["center"][1])
            else:
                same_col = [h for h in headers if h["col"] == col]
                mh = min(same_col, key=lambda h: abs(h["center"][1] - cy))

            month_num = MONTH_NUM_MAP[mh["month"]]
            try:
                dt = datetime.date(mh["year"], month_num, day)
            except ValueError:
                continue

            if (dt, waste_type) not in seen:
                seen.add((dt, waste_type))
                entries.append(
                    Collection(date=dt, t=waste_type, icon=ICON_MAP.get(waste_type))
                )

            if (dt, "General Waste") not in seen:
                seen.add((dt, "General Waste"))
                entries.append(
                    Collection(
                        date=dt,
                        t="General Waste",
                        icon=ICON_MAP.get("General Waste"),
                    )
                )

    return entries


def _extract_bulky_events_from_pdf(pdf_bytes: bytes) -> list[Collection]:
    """Extract bulky waste dates from the bulky waste flyer PDF."""
    text_parts: list[str] = []
    reader = PdfReader(BytesIO(pdf_bytes))
    for page in reader.pages:
        try:
            text_parts.append(page.extract_text() or "")
        except Exception:
            continue
    text = "\n".join(text_parts)

    rx = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
    seen: set[datetime.date] = set()
    entries: list[Collection] = []

    for m in rx.finditer(text):
        day_s, month_s, year_s = m.groups()
        year = int(year_s)
        if year < 100:
            year += 2000
        try:
            dt = datetime.date(year, int(month_s), int(day_s))
        except ValueError:
            continue
        if dt in seen:
            continue
        seen.add(dt)
        entries.append(
            Collection(date=dt, t="Bulky Waste", icon=ICON_MAP.get("Bulky Waste"))
        )

    return entries


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        html = _fetch_waste_services_html(self._address)
        if not html.strip():
            return []

        # Primary: parse dates from the HTML widget
        entries = _extract_entries_from_html(html)

        # Extract PDF hrefs from the HTML for fallback/supplement
        parser = _WasteServiceParser()
        parser.feed(html)

        # If HTML didn't yield green waste or recycling, try the weekly PDF
        html_types = {e.type for e in entries}
        if not {"Green Waste", "Recycling"}.issubset(html_types):
            weekly_href = _select_weekly_waste_calendar_pdf_href(parser.hrefs)
            if weekly_href:
                weekly_url = urllib.parse.urljoin(BASE_URL, weekly_href)
                try:
                    weekly_bytes = _http_get(weekly_url)
                    pdf_entries = _extract_events_from_weekly_pdf(weekly_bytes)
                    for e in pdf_entries:
                        if e.type not in html_types:
                            entries.append(e)
                except Exception as exc:
                    _LOGGER.warning("Failed to extract weekly calendar PDF: %s", exc)

        # If HTML didn't yield bulky waste, try the bulky PDF
        if "Bulky Waste" not in html_types:
            bulky_href = _select_bulky_waste_calendar_pdf_href(parser.hrefs)
            if bulky_href:
                bulky_url = urllib.parse.urljoin(BASE_URL, bulky_href)
                try:
                    bulky_bytes = _http_get(bulky_url)
                    entries.extend(_extract_bulky_events_from_pdf(bulky_bytes))
                except Exception as exc:
                    _LOGGER.warning(
                        "Failed to extract bulky waste calendar PDF: %s", exc
                    )

        entries.sort(key=lambda e: e.date)
        return entries
