"""
Orange City Council (NSW, Australia) waste collection source.

The council's annual waste booklet (PDF) is a zone reference guide — it shows
which streets belong to Week A or Week B collection, but does NOT contain a
date calendar.  Collection dates are therefore calculated mathematically:

  - General Waste (red/dark lid): every Wednesday
  - Recycling (yellow lid):       fortnightly Wednesdays, alternating Week A / Week B

The PDF is fetched at runtime solely to confirm the current booklet year so
that the correct calendar year is used when building the schedule.

Data source: https://www.orange.nsw.gov.au/waste/
"""

from __future__ import annotations

import datetime
import io
import logging
import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Orange City Council"
DESCRIPTION = (
    "Source for Orange City Council (NSW, Australia) residential waste collection."
)
URL = "https://www.orange.nsw.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Week A (west of Anson Street) - e.g. Molloy Drive": {"zone": "A"},
    "Week B (east of Anson Street, Spring Hill, Lucknow, Clifton Grove)": {"zone": "B"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Orange City Council divides the city into two fortnightly recycling zones "
        "(referred to in the waste booklet as Week A and Week B). "
        "Zone A covers properties west of Anson Street. "
        "Zone B covers properties east of Anson Street, properties on Anson Street, "
        "Spring Hill, Lucknow, and Clifton Grove. "
        "Download the annual waste booklet from https://www.orange.nsw.gov.au/waste/ "
        "to confirm which zone your street belongs to."
    ),
}

_WASTE_PAGE_URL = "https://www.orange.nsw.gov.au/waste/"

# Matches the waste booklet PDF URL embedded in the council page HTML
_PDF_LINK_RE = re.compile(
    r'https?://[^\s"\'<>]*WasteBooklet[^\s"\'<>]*\.pdf',
    re.IGNORECASE,
)

# Pulls a 4-digit year from the PDF URL (e.g. "…2026…")
_YEAR_IN_URL_RE = re.compile(r"\b(20\d{2})\b")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; waste-collection-schedule)",
    "Accept-Language": "en-AU,en;q=0.9",
}


def _find_pdf_url(session: requests.Session) -> str:
    """Scrape the council waste page and return the current booklet PDF URL."""
    resp = session.get(_WASTE_PAGE_URL, timeout=30, headers=_HEADERS)
    resp.raise_for_status()
    match = _PDF_LINK_RE.search(resp.text)
    if match:
        return match.group(0)
    raise ValueError(
        f"Could not find the waste booklet PDF link on {_WASTE_PAGE_URL}. "
        "The page layout may have changed — please raise an issue."
    )


def _year_from_pdf_url(url: str) -> int | None:
    """Extract the booklet year from the PDF URL, e.g. '…2026…'."""
    m = _YEAR_IN_URL_RE.search(url)
    return int(m.group(1)) if m else None


def _year_from_pdf_text(session: requests.Session, url: str) -> int | None:
    """
    Download the first page of the PDF and look for a 4-digit year in the text.
    Used as a fallback when the year cannot be determined from the URL alone.
    """
    try:
        from pypdf import PdfReader  # type: ignore[import]
    except ImportError:
        return None

    try:
        resp = session.get(
            url, timeout=60, headers={**_HEADERS, "Referer": _WASTE_PAGE_URL}
        )
        resp.raise_for_status()
        reader = PdfReader(io.BytesIO(resp.content))
        # Check the first two pages — the cover page carries the year
        for page in reader.pages[:2]:
            text = page.extract_text() or ""
            m = _YEAR_IN_URL_RE.search(text)
            if m:
                return int(m.group(1))
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug(
            "orange_nsw_gov_au: Could not extract year from PDF text: %s", exc
        )
    return None


def _build_schedule(zone: str, year: int) -> list[Collection]:
    """
    Build the full collection schedule for *zone* in *year*.

    General Waste  — every Wednesday
    Recycling      — fortnightly Wednesdays
                     Zone A: starts on the 1st Wednesday of the year
                     Zone B: starts on the 2nd Wednesday of the year
    """
    entries: list[Collection] = []

    # First Wednesday of the year
    first_day = datetime.date(year, 1, 1)
    days_to_wed = (2 - first_day.weekday()) % 7
    first_wednesday = first_day + datetime.timedelta(days=days_to_wed)

    # Zone B starts one week later than Zone A
    recycling_start = (
        first_wednesday
        if zone.upper() == "A"
        else first_wednesday + datetime.timedelta(weeks=1)
    )

    d = first_wednesday
    while d.year == year:
        entries.append(
            Collection(date=d, t="General Waste", icon=ICON_MAP["General Waste"])
        )
        d += datetime.timedelta(weeks=1)

    d = recycling_start
    while d.year == year:
        entries.append(Collection(date=d, t="Recycling", icon=ICON_MAP["Recycling"]))
        d += datetime.timedelta(weeks=2)

    return entries


class Source:
    """Waste collection source for Orange City Council, NSW, Australia."""

    def __init__(self, zone: str) -> None:
        self._zone = zone.strip().upper()
        if self._zone not in ("A", "B"):
            raise ValueError(
                f"Invalid zone '{zone}'. Must be 'A' (west of Anson Street) or "
                "'B' (east of Anson Street / Spring Hill / Lucknow / Clifton Grove)."
            )

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # --- Determine the current booklet year ---
        year: int | None = None
        try:
            pdf_url = _find_pdf_url(session)
            _LOGGER.debug("orange_nsw_gov_au: Booklet PDF URL = %s", pdf_url)
            year = _year_from_pdf_url(pdf_url)
            if year is None:
                year = _year_from_pdf_text(session, pdf_url)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning(
                "orange_nsw_gov_au: Could not fetch booklet from %s (%s). "
                "Falling back to current calendar year.",
                _WASTE_PAGE_URL,
                exc,
            )

        if year is None:
            year = datetime.date.today().year
            _LOGGER.warning(
                "orange_nsw_gov_au: Could not determine booklet year — using %d.", year
            )
        else:
            _LOGGER.debug("orange_nsw_gov_au: Schedule year = %d", year)

        return _build_schedule(self._zone, year)
