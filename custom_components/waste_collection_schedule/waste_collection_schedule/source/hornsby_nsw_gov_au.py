from __future__ import annotations

import datetime
import json
import logging
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from html.parser import HTMLParser
from typing import Any

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

BASE_URL = "https://www.hornsby.nsw.gov.au/"

_LOGGER = logging.getLogger(__name__)


def _http_get(url: str, timeout_s: float = 25.0) -> bytes:
    """Perform an HTTP GET request and return the response body."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
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


def _extract_events_from_weekly_pdf(pdf_bytes: bytes) -> list[Collection]:
    """Extract green waste and recycling events from the weekly calendar PDF."""
    try:
        import fitz  # PyMuPDF
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "PyMuPDF (fitz) and numpy are required for PDF extraction. "
            "Please install them with: pip install pymupdf numpy"
        ) from e

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if doc.page_count < 1:
        raise ValueError("Empty PDF")

    page = doc[0]

    # Extract month headers
    rx = re.compile(
        r"^(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|"
        r"OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})$"
    )

    text = page.get_text("dict")
    headers: list[dict[str, Any]] = []

    for block in text.get("blocks", []):
        for line in block.get("lines", []):
            line_text = "".join(
                span["text"] for span in line.get("spans", [])
            ).strip()
            m = rx.match(line_text)
            if not m:
                continue

            bbox = fitz.Rect(line["bbox"])
            center = ((bbox.x0 + bbox.x1) / 2.0, (bbox.y0 + bbox.y1) / 2.0)
            headers.append(
                {
                    "month": m.group(1),
                    "year": int(m.group(2)),
                    "bbox": bbox,
                    "center": center,
                    "col": None,
                }
            )

    if not headers:
        raise ValueError("No month headers found in PDF.")

    # Assign columns to headers using k-means-like clustering
    ncols = 4
    xs = np.array([h["center"][0] for h in headers])
    seeds = np.quantile(xs, np.linspace(0.1, 0.9, ncols))
    centers = seeds.copy()

    for _ in range(10):
        idx = np.argmin(np.abs(xs[:, None] - centers[None, :]), axis=1)
        new_centers = centers.copy()
        for c in range(ncols):
            members = xs[idx == c]
            if len(members) > 0:
                new_centers[c] = float(np.mean(members))
        if np.allclose(new_centers, centers, atol=0.5):
            centers = new_centers
            break
        centers = new_centers

    col_centers = sorted([float(c) for c in centers])

    for h in headers:
        h["col"] = int(np.argmin([abs(h["center"][0] - c) for c in col_centers]))

    # Extract digit words
    digit_words: list[tuple[int, Any]] = []
    for x0, y0, x1, y1, txt, *_ in page.get_text("words"):
        if re.fullmatch(r"\d{1,2}", txt):
            digit_words.append((int(txt), fitz.Rect(x0, y0, x1, y1)))

    # Extract marker shapes
    drawings = page.get_drawings()
    cand: list[dict] = []
    for d in drawings:
        fill = d.get("fill")
        if fill is None or _is_near_white(fill):
            continue
        r = d["rect"]
        w = r.x1 - r.x0
        h = r.y1 - r.y0
        if 10.0 < w < 25.0 and 10.0 < h < 25.0:
            cand.append(d)

    by_fill: dict[tuple[float, float, float], list[dict]] = defaultdict(list)
    for d in cand:
        by_fill[d["fill"]].append(d)

    marker_sets: dict[str, list[dict]] = {}
    for fill, items in by_fill.items():
        label = _classify_fill(fill)
        if label == "unknown":
            continue

        sizes = np.array(
            [
                [it["rect"].x1 - it["rect"].x0, it["rect"].y1 - it["rect"].y0]
                for it in items
            ]
        )
        med = np.median(sizes, axis=0)

        keep: list[dict] = []
        for it in items:
            r = it["rect"]
            w = r.x1 - r.x0
            h = r.y1 - r.y0
            if abs(w - med[0]) < 2.0 and abs(h - med[1]) < 2.0:
                keep.append(it)

        if len(keep) >= 10:
            marker_sets[label] = keep

    if not {"green", "yellow"}.issubset(marker_sets.keys()):
        raise ValueError(
            f"Could not detect both marker sets. Detected={list(marker_sets.keys())}"
        )

    month_num_map = {
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

    entries: list[Collection] = []
    seen: set[tuple[str, str]] = set()

    for color, markers in marker_sets.items():
        for m in markers:
            marker_rect = m["rect"]
            cx = (marker_rect.x0 + marker_rect.x1) / 2.0
            cy = (marker_rect.y0 + marker_rect.y1) / 2.0

            # Find the day number
            day = None
            for d, wrect in digit_words:
                if wrect.contains(fitz.Point(cx, cy)):
                    day = d
                    break
            if day is None:
                best_score = -1.0
                for d, wrect in digit_words:
                    inter = marker_rect & wrect
                    if not inter.is_empty:
                        score = inter.get_area()
                        if score > best_score:
                            best_score = score
                            day = d
            if day is None:
                continue

            # Find the month
            col = min(
                range(len(col_centers)), key=lambda i: abs(cx - col_centers[i])
            )
            candidates = [h for h in headers if h["col"] == col and h["center"][1] <= cy + 1.0]
            if candidates:
                mh = max(candidates, key=lambda h: h["center"][1])
            else:
                same_col = [h for h in headers if h["col"] == col]
                mh = min(same_col, key=lambda h: abs(h["center"][1] - cy))

            month_num = month_num_map[mh["month"]]
            try:
                date = datetime.date(mh["year"], month_num, day)
            except ValueError:
                continue

            if color == "green":
                waste_type = "Green Waste"
            else:
                waste_type = "Recycling"

            key = (date.isoformat(), waste_type)
            if key in seen:
                continue
            seen.add(key)

            entries.append(
                Collection(date=date, t=waste_type, icon=ICON_MAP.get(waste_type))
            )

            # General Waste is collected on both green and recycling days
            gen_key = (date.isoformat(), "General Waste")
            if gen_key not in seen:
                seen.add(gen_key)
                entries.append(
                    Collection(
                        date=date, t="General Waste", icon=ICON_MAP.get("General Waste")
                    )
                )

    doc.close()
    return entries


def _extract_bulky_events_from_pdf(pdf_bytes: bytes) -> list[Collection]:
    """Extract bulky waste dates from the bulky waste flyer PDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF extraction. "
            "Please install it with: pip install pymupdf"
        ) from e

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts: list[str] = []
    for page in doc:
        try:
            text_parts.append(page.get_text("text"))
        except Exception:
            continue
    text = "\n".join(text_parts)
    doc.close()

    rx = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
    seen: set[str] = set()
    entries: list[Collection] = []

    for m in rx.finditer(text):
        day_s, month_s, year_s = m.groups()
        day = int(day_s)
        month = int(month_s)
        year = int(year_s)
        if year < 100:
            year += 2000
        try:
            d = datetime.date(year, month, day)
        except ValueError:
            continue
        iso = d.isoformat()
        if iso in seen:
            continue
        seen.add(iso)
        entries.append(
            Collection(date=d, t="Bulky Waste", icon=ICON_MAP.get("Bulky Waste"))
        )

    return entries


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        # Resolve PDF URLs for the address
        urls = _resolve_pdf_urls_for_address(self._address)

        entries: list[Collection] = []

        # Download and extract weekly calendar
        if urls["weekly"]:
            weekly_bytes = _http_get(urls["weekly"])
            entries.extend(_extract_events_from_weekly_pdf(weekly_bytes))

        # Download and extract bulky waste calendar
        if urls.get("bulky"):
            bulky_bytes = _http_get(urls["bulky"])
            entries.extend(_extract_bulky_events_from_pdf(bulky_bytes))

        # Sort by date
        entries.sort(key=lambda e: e.date)
        return entries
