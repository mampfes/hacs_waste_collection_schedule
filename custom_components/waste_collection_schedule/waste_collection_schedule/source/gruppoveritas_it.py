import logging
import re
from datetime import date
from io import BytesIO

import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

_LOGGER = logging.getLogger(__name__)

TITLE = "Gruppo Veritas"
DESCRIPTION = "Waste collection schedules published as PDF calendars by Gruppo Veritas (Jesolo and other municipalities)."
URL = "https://www.gruppoveritas.it/"
COUNTRY = "it"

DEFAULT_PDF_URL = (
    "https://www.gruppoveritas.it/sites/default/files/documenti/calendari/"
    "jesolo_calendario_raccolta_differenziata_2026.pdf"
)

# Waste-type badge codes printed in the calendar legend.
#
# Known PDF rendering artefact: the VR (Verde/Ramaglie) badge may occasionally
# be extracted as "VPL" when it appears inline as part of a postponement note
# (e.g. "VPL RACCOLTA POSTICIPATA AL 5" instead of "VR RACCOLTA POSTICIPATA AL 5").
# This is caused by identical glyph shapes in the embedded PDF font and cannot
# be corrected in the parser; the affected postponed collection will be
# attributed to Vetro/Plastica/Lattine rather than Verde/Ramaglie.
CODE_MAP = {
    "C": "Carta/Cartone",
    "VPL": "Vetro/Plastica/Lattine",
    "S": "Secco",
    "UO": "Umido/Organico",
    "VR": "Verde/Ramaglie",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "pdf_url": "Direct URL to the PDF calendar published on the Gruppo Veritas website.",
        "year": "Calendar year to extract (must match the year inside the PDF).",
    },
    "it": {
        "pdf_url": "URL diretto del calendario PDF pubblicato sul sito di Gruppo Veritas.",
        "year": "Anno del calendario da estrarre (deve corrispondere all'anno nel PDF).",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "pdf_url": "PDF Calendar URL",
        "year": "Year",
    },
    "de": {
        "pdf_url": "PDF-Kalender URL",
        "year": "Jahr",
    },
    "it": {
        "pdf_url": "URL Calendario PDF",
        "year": "Anno",
    },
    "fr": {
        "pdf_url": "URL du calendrier PDF",
        "year": "Année",
    },
}

ICON_MAP = {
    "Carta/Cartone": Icons.PAPER,
    "Vetro/Plastica/Lattine": Icons.GLASS,
    "Secco": Icons.GENERAL_WASTE,
    "Umido/Organico": Icons.ORGANIC,
    "Verde/Ramaglie": Icons.GARDEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.gruppoveritas.it, navigate to your municipality's waste "
        "collection page, locate the PDF calendar download link, and paste its URL "
        "into the pdf_url field."
    ),
    "it": (
        "Apri https://www.gruppoveritas.it, vai alla pagina del tuo Comune, "
        "trova il link al calendario PDF e incolla l'URL nel campo pdf_url."
    ),
}

TEST_CASES = {
    "Jesolo_2026": {
        "pdf_url": DEFAULT_PDF_URL,
        "year": 2026,
    },
}

# ── Italian month names ───────────────────────────────────────────────────────

_ITALIAN_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

# ── Regular expressions ───────────────────────────────────────────────────────

_MONTH_NAME_RE = re.compile(
    r"\b(" + "|".join(_ITALIAN_MONTHS.keys()) + r")\b",
    re.IGNORECASE,
)

# Matches the start of a calendar day row: optional leading whitespace,
# a 1-2 digit day number, then an Italian weekday abbreviation.
# Everything after the weekday is captured as optional trailing text.
_DAY_RE = re.compile(r"^\s*(\d{1,2})\s+(?:LUN|MAR|MER|GIO|VEN|SAB|DOM)(.*?)$")

_CODES_RE = re.compile(r"\b(VPL|UO|VR|S|C)\b")
_SUSPEND_RE = re.compile(r"\bSOSPESA\b", re.IGNORECASE)
_POSTPONE_RE = re.compile(
    r"\bPOSTICIPATA\s+AL\s+(\d{1,2})(?:/(\d{1,2}))?\b",
    re.IGNORECASE,
)

# The calendar header prints a two-digit year suffix on a line that begins
# with that suffix followed by whitespace
# (e.g. "26   PORTA A PORTA" signals year 2026).
_YEAR_TOKEN_RE = re.compile(r"^\s*(2[5-9])\s")

# Column split character index for pypdf extraction_mode="layout" output.
#
# Each calendar page contains two months side-by-side. pypdf layout mode
# reproduces the spatial arrangement so that both months appear on the same
# line separated by whitespace. Empirically, position 133 cleanly separates
# the left and right month columns across all calendar pages in this PDF family.
_COL_SPLIT = 133

# Lines whose stripped text contains any of these strings belong to the
# footer/legend zone at the bottom of each page. Parsing of the current
# pending day stops immediately when one is encountered, preventing legend
# badge codes (C, VPL, S, UO, VR) from being attributed to the last day.
_FOOTER_MARKERS = (
    "CITTÀ DI JESOLO",
    "LUN e SAB",
    "CENTRO di RACCOLTA",
    "VETRO",  # first word of the badge legend ("VETRO / PLASTICA / LATTINE …")
)

# A continuation line that contains ONLY one or more waste-type codes and
# nothing else is a pypdf layout artefact: the code belonging to the NEXT
# day's suspended/postponed note has been placed on a separate line before
# that day's number. We skip such lines when the pending day already has at
# least one code, so they are not incorrectly attributed to the previous day.
#
# Example (giugno, colonna destra):
#   [row]  "1  LUN  VR"        <- pending = (1, ["VR"])
#   [row]  "UO"                <- artefact: belongs to day 2's SOSPESA note
#   [row]  "2  MAR  RACCOLTA SOSPESA"
#
# Without this guard, day 1 would get both VR and UO.
_ONLY_CODES_RE = re.compile(r"^\s*(VPL|UO|VR|S|C)(\s+(VPL|UO|VR|S|C))*\s*$")


# ── PDF download ──────────────────────────────────────────────────────────────


def _download_pdf(url: str) -> BytesIO:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return BytesIO(r.content)


# ── Per-column event parser ───────────────────────────────────────────────────


def _parse_column(col_lines, month, year):
    """Parse one column of pypdf layout-mode lines into (date, waste_type) pairs.

    Layout:
    - A day starts with _DAY_RE (number + weekday abbreviation).
    - Subsequent non-empty lines until the next day match are continuation
      notes, e.g. "RACCOLTA SOSPESA" or "POSTICIPATA AL 28/12".
    - A line containing ONLY waste-type codes (e.g. just "UO") while the
      pending day already has codes is a layout artefact and is skipped.
    """
    groups = []
    pending = None

    for raw in col_lines:
        stripped = raw.strip()
        m = _DAY_RE.match(stripped)
        if m:
            if pending is not None:
                groups.append(pending)
            day_num = int(m.group(1))
            trailing = m.group(2).strip()
            pending = (day_num, [trailing] if trailing else [])
        elif stripped and pending is not None:
            if any(marker in stripped for marker in _FOOTER_MARKERS):
                pending = None
                break
            # Skip orphaned code-only lines: a line containing nothing but
            # waste-type codes (e.g. just "UO") is always a pypdf layout
            # artefact where the code of the *next* day's SOSPESA/POSTICIPATA
            # note has been placed on a separate line before that day's number.
            # This applies regardless of whether the pending day already has
            # codes, so we skip unconditionally.
            if _ONLY_CODES_RE.match(stripped):
                continue
            pending[1].append(stripped)

    if pending is not None:
        groups.append(pending)

    events = []
    for day_num, notes in groups:
        combined = " ".join(notes)
        codes = list(set(_CODES_RE.findall(combined)))

        pm = _POSTPONE_RE.search(combined)
        if pm:
            target_day = int(pm.group(1))
            target_month_raw = pm.group(2)
            target_month = int(target_month_raw) if target_month_raw else month
            # If the explicit target month is earlier than current, it crosses
            # into the next year (e.g. a December postponement to January).
            target_year = (
                year + 1 if target_month_raw and target_month < month else year
            )
            try:
                dt = date(target_year, target_month, target_day)
                for c in codes:
                    events.append((dt, CODE_MAP.get(c, c)))
            except ValueError:
                _LOGGER.warning(
                    "Invalid postponed date: day=%d month=%d year=%d",
                    target_day,
                    target_month,
                    target_year,
                )
            continue

        if _SUSPEND_RE.search(combined):
            continue

        try:
            dt = date(year, month, day_num)
        except ValueError:
            _LOGGER.debug(
                "Skipping invalid date: day=%d month=%d year=%d",
                day_num,
                month,
                year,
            )
            continue

        for c in codes:
            events.append((dt, CODE_MAP.get(c, c)))

    return events


# ── Page parser ───────────────────────────────────────────────────────────────


def _parse_page(page, fallback_year):
    """Parse one PDF page into (date, waste_type) pairs.

    Each calendar page shows two months side-by-side. pypdf
    ``extraction_mode="layout"`` reproduces the spatial arrangement so both
    months appear on the same text lines separated by whitespace. Splitting
    at ``_COL_SPLIT`` cleanly separates the two columns.
    """
    try:
        txt = page.extract_text(extraction_mode="layout") or ""
    except Exception:
        txt = page.extract_text() or ""

    lines = txt.split("\n")

    # Detect year from the large two-digit suffix in the page header
    # (e.g. the line "26   PORTA A PORTA" signals year 2026).
    year = fallback_year
    for line in lines[:4]:
        ym = _YEAR_TOKEN_RE.match(line)
        if ym:
            year = int("20" + ym.group(1))
            break

    # Detect left and right month names from the header area.
    left_month = None
    right_month = None
    for line in lines[:10]:
        left_part = line[:_COL_SPLIT]
        right_part = line[_COL_SPLIT:] if len(line) > _COL_SPLIT else ""
        if left_month is None:
            ml = _MONTH_NAME_RE.search(left_part)
            if ml:
                left_month = _ITALIAN_MONTHS[ml.group(1).lower()]
        if right_month is None:
            mr = _MONTH_NAME_RE.search(right_part)
            if mr:
                right_month = _ITALIAN_MONTHS[mr.group(1).lower()]
        if left_month and right_month:
            break

    if left_month is None:
        return []  # Not a calendar page.

    left_col = [line[:_COL_SPLIT] for line in lines]
    right_col = [line[_COL_SPLIT:] if len(line) > _COL_SPLIT else "" for line in lines]

    events = _parse_column(left_col, left_month, year)
    if right_month:
        events.extend(_parse_column(right_col, right_month, year))

    _LOGGER.debug(
        "Page parsed: months=(%s, %s) year=%d events=%d",
        left_month,
        right_month,
        year,
        len(events),
    )
    return events


# ── Top-level parser ──────────────────────────────────────────────────────────


def _parse_pdf(pdf_bytes: BytesIO, target_year: int) -> list:
    reader = PdfReader(pdf_bytes)
    all_events = []

    for page in reader.pages:
        all_events.extend(_parse_page(page, target_year))

    # Keep only events for the requested year (the PDF may include a partial
    # preview of the following year starting from December).
    all_events = [(dt, wt) for dt, wt in all_events if dt.year == target_year]

    # Deduplicate and sort.
    unique = {(dt, wt): (dt, wt) for dt, wt in all_events}
    return sorted(unique.values(), key=lambda e: (e[0], e[1]))


# ── Source class ──────────────────────────────────────────────────────────────


class Source:
    def __init__(self, pdf_url: str = DEFAULT_PDF_URL, year: int = 2026):
        if not pdf_url:
            raise SourceArgumentNotFound("pdf_url", "pdf_url")
        self._pdf_url = pdf_url
        self._year = year

    def fetch(self):
        pdf_bytes = _download_pdf(self._pdf_url)
        events = _parse_pdf(pdf_bytes, self._year)

        if not events:
            raise ValueError(
                f"No collection events found for year {self._year} in the PDF at "
                f"{self._pdf_url}. Check that pdf_url points to the correct calendar "
                "and that year matches."
            )

        _LOGGER.debug("Fetched %d collection events for %d.", len(events), self._year)
        return [Collection(date=dt, t=wt, icon=ICON_MAP.get(wt)) for dt, wt in events]
