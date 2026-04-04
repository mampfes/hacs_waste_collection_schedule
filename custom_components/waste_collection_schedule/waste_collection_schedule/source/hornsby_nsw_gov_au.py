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
    LTAnno,
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

BASE_URL = "https://www.hornsby.nsw.gov.au/"

_LOGGER = logging.getLogger(__name__)


def _http_get(url: str, timeout_s: float = 25.0) -> bytes:
    """Perform an HTTP GET request and return the response body."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Referer": "https://www.hornsby.nsw.gov.au/",
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

    # Sort by score (highest first) and return the best match
    items.sort(key=lambda r: r.get("Score", 0), reverse=True)
    return items[0]["Id"]


class _HrefExtractor(HTMLParser):
    """Simple HTML parser to extract href attributes from anchor tags."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        d = {k.lower(): v for k, v in attrs}
        href = d.get("href")
        if href:
            self.hrefs.append(href)


def _select_weekly_waste_calendar_pdf_href(hrefs: list[str]) -> str | None:
    """Select the weekly waste calendar PDF URL from the list of hrefs."""
    pdfs = [h for h in hrefs if h.lower().endswith(".pdf")]
    if not pdfs:
        return None

    # Strong signal: weekly waste calendar under 'suds-waste-and-recycling'
    cand = [
        h
        for h in pdfs
        if "collection-calendars" in h and "suds-waste-and-recycling" in h
    ]
    if cand:
        return cand[0]

    # Fallback: any collection-calendars PDF that doesn't look like bulky-waste
    cand = [
        h
        for h in pdfs
        if "collection-calendars" in h
        and "bulky" not in h.lower()
        and "suds-bulky-waste" not in h.lower()
    ]
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
        or ("bulkywasteflyer" in h.lower())
        or ("bulkywaste" in h.lower())
    ]
    if preferred:
        return preferred[0]

    cand = [h for h in pdfs if "bulky" in h.lower()]
    if cand:
        return cand[0]

    return None


def _resolve_pdf_urls_for_address(
    address: str, language: str = "en-AU"
) -> dict[str, str | None]:
    """Resolve the PDF URLs for a given address via Hornsby Council API."""
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

    html = ws_json.get("responseContent") or ""
    if not html.strip():
        # No waste services content - address may not have collection services
        return {"weekly": None, "bulky": None}

    parser = _HrefExtractor()
    parser.feed(html)

    weekly_href = _select_weekly_waste_calendar_pdf_href(parser.hrefs)
    bulky_href = _select_bulky_waste_calendar_pdf_href(parser.hrefs)

    weekly_url = urllib.parse.urljoin(BASE_URL, weekly_href) if weekly_href else None
    bulky_url = urllib.parse.urljoin(BASE_URL, bulky_href) if bulky_href else None

    return {"weekly": weekly_url, "bulky": bulky_url}


def _is_near_white(rgb: tuple[float, float, float]) -> bool:
    """Check if an RGB color is near white."""
    r, g, b = rgb
    return r > 0.95 and g > 0.95 and b > 0.95


def _classify_fill(rgb: tuple[float, float, float]) -> str:
    """Classify fill color into 'green' or 'yellow'."""
    r, g, b = rgb
    if g > 0.45 and r < 0.45 and b < 0.45:
        return "green"
    if r > 0.70 and g > 0.55 and b < 0.45:
        return "yellow"
    return "unknown"


def _normalize_color_to_rgb(
    color: Any,
) -> tuple[float, float, float] | None:
    """Normalize a pdfminer color value to an (r, g, b) tuple with values 0–1."""
    if color is None:
        return None
    if isinstance(color, (list, tuple)):
        if len(color) == 3:
            # DeviceRGB
            return (float(color[0]), float(color[1]), float(color[2]))
        if len(color) == 4:
            # DeviceCMYK → convert to RGB
            c, m, y, k = (float(v) for v in color)
            return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
        if len(color) == 1:
            # Grayscale
            g = float(color[0])
            return (g, g, g)
    if isinstance(color, (int, float)):
        # Grayscale scalar
        g = float(color)
        return (g, g, g)
    return None


def _iter_layout_elements(container: Any) -> Any:
    """Recursively yield all layout elements from a pdfminer container."""
    for element in container:
        yield element
        if isinstance(element, LTLayoutContainer):
            yield from _iter_layout_elements(element)


def _flush_word(
    word_chars: list[LTChar], page_height: float
) -> dict[str, Any]:
    """Build a word dict from a list of LTChar objects using top-origin coordinates."""
    word_text = "".join(c.get_text() for c in word_chars)
    bx0 = min(c.bbox[0] for c in word_chars)
    by0 = min(c.bbox[1] for c in word_chars)
    bx1 = max(c.bbox[2] for c in word_chars)
    by1 = max(c.bbox[3] for c in word_chars)
    return {
        "text": word_text,
        "x0": bx0,
        "x1": bx1,
        # Convert bottom-origin → top-origin
        "top": page_height - by1,
        "bottom": page_height - by0,
    }


def _extract_words_from_page(
    page_layout: Any, page_height: float
) -> list[dict[str, Any]]:
    """Extract words with top-origin bounding boxes from a pdfminer page layout."""
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
    """Group word dicts into text lines by proximity of their 'top' coordinate."""
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

    page = pages[0]
    page_height = float(page.height)

    # Extract month headers
    rx = re.compile(
        r"^(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|"
        r"OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})$"
    )

    words = _extract_words_from_page(page, page_height)
    text_lines = _group_words_into_lines(words)
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
                "month": m.group(1),
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
    # Initial seeds at evenly-spaced quantiles
    centers = [
        xs_sorted[min(int(q * (n - 1) + 0.5), n - 1)]
        for q in (0.1 + i * 0.8 / (ncols - 1) for i in range(ncols))
    ]

    for _ in range(10):
        assignments = [
            min(range(ncols), key=lambda c: abs(x - centers[c])) for x in xs
        ]
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

    # Extract digit words (day numbers) with their bounding boxes
    digit_words: list[tuple[int, dict[str, Any]]] = [
        (int(w["text"]), w)
        for w in words
        if re.fullmatch(r"\d{1,2}", w["text"])
    ]

    # Extract marker shapes (coloured squares that indicate collection type)
    # pdfminer.six exposes LTRect with non_stroking_color for the fill colour
    by_fill: dict[str, list[dict[str, Any]]] = {}
    for element in _iter_layout_elements(page):
        if not isinstance(element, LTRect):
            continue
        rgb = _normalize_color_to_rgb(element.non_stroking_color)
        if rgb is None or _is_near_white(rgb):
            continue
        bx0, by0, bx1, by1 = element.bbox
        # Convert bottom-origin → top-origin
        top_coord = page_height - by1
        bottom_coord = page_height - by0
        rect_w = bx1 - bx0
        rect_h = by1 - by0
        if not (10.0 < rect_w < 25.0 and 10.0 < rect_h < 25.0):
            continue
        label = _classify_fill(rgb)
        if label != "unknown":
            by_fill.setdefault(label, []).append(
                {
                    "x0": bx0,
                    "x1": bx1,
                    "top": top_coord,
                    "bottom": bottom_coord,
                }
            )

    # Filter markers to consistent sizes using median
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

            # Find the day number — first try containment, then overlap
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
                    # Compute intersection area
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

            # Find the month header for this marker
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

            # General Waste is collected on both green and recycling weeks
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
        urls = _resolve_pdf_urls_for_address(self._address)
        entries: list[Collection] = []

        if urls["weekly"]:
            try:
                weekly_bytes = _http_get(urls["weekly"])
                entries.extend(_extract_events_from_weekly_pdf(weekly_bytes))
            except Exception as e:
                _LOGGER.warning("Failed to extract weekly calendar: %s", e)

        if urls["bulky"]:
            try:
                bulky_bytes = _http_get(urls["bulky"])
                entries.extend(_extract_bulky_events_from_pdf(bulky_bytes))
            except Exception as e:
                _LOGGER.warning("Failed to extract bulky waste calendar: %s", e)

        entries.sort(key=lambda e: e.date)
        return entries
