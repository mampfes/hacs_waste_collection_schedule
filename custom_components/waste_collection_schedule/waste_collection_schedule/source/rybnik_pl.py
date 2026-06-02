import logging
import re
import unicodedata
from datetime import date, datetime
from io import BytesIO

import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Rybnik"
DESCRIPTION = (
    "Source for Rybnik (Poland) municipal waste collection schedules "
    "provided by EKO Sp. z o.o."
)
URL = "https://www.rybnik.eu"

_BASE_URL = (
    "https://www.rybnik.eu/fileadmin/user_files/mieszkaj/samorzad/"
    "odpady_komunalne/Harmonogramy_{year}/"
)

# Each district maps to:
#   slug          — the URL-slug used in the PDF filename
#   zones         — the canonical Rejon (zone) names that appear in the cover-page
#                   table on page 1. The order MUST match the visual top-to-bottom
#                   order of the schedule blocks on page 2.
#   zone_aliases  — optional dict of {canonical_name: [extra strings]} for cases
#                   where the page-2 footer abbreviates a zone name (e.g.
#                   "Kuźnia" on page 2 vs "Kuźnia Rybnicka" on page 1).
DISTRICT_MAP: dict[str, dict] = {
    "Boguszowice Stare": {
        "slug": "Boguszowice_Stare",
        "zones": [f"Boguszowice Stare {i}" for i in range(1, 6)],
    },
    "Chwalowice / Boguszowice Os. / Klokocin": {
        "slug": "Chwalowice__Boguszowice_Os.__Klokocin",
        "zones": [
            "Chwałowice 1",
            "Chwałowice 2",
            "Boguszowice Osiedle",
            "Kłokocin 1",
            "Kłokocin 2",
        ],
    },
    "Gotartowice": {
        "slug": "Gotartowice",
        "zones": [f"Gotartowice {i}" for i in range(1, 5)],
    },
    "Grabownia / Golejow / Ochojec": {
        "slug": "Grabownia__Golejow__Ochojec",
        "zones": [
            "Grabownia",
            "Golejów 1",
            "Golejów 2",
            "Ochojec 1",
            "Ochojec 2",
        ],
    },
    "Ligota": {
        "slug": "Ligota",
        "zones": [f"Ligota-Ligocka Kuźnia {i}" for i in range(1, 5)],
    },
    "Maroko-Nowiny": {
        "slug": "Maroko-Nowiny",
        "zones": [f"Maroko-Nowiny {i}" for i in range(1, 7)],
    },
    "Niedobczyce": {
        "slug": "Niedobczyce",
        "zones": [f"Niedobczyce {i}" for i in range(1, 8)],
    },
    "Niewiadom": {
        "slug": "Niewiadom",
        "zones": [f"Niewiadom {i}" for i in range(1, 5)],
    },
    "Orzepowice / Stodoly / Chwalecice": {
        "slug": "Orzepowice__Stodoly__Chwalecice",
        "zones": [
            "Orzepowice 1",
            "Orzepowice 2",
            "Stodoły",
            "Chwałęcice 1",
            "Chwałęcice 2",
        ],
    },
    "Paruszowiec / Kamien": {
        "slug": "Paruszowiec__Kamien",
        "zones": [
            "Paruszowiec-Piaski",
            "Kamień 1",
            "Kamień 2",
        ],
    },
    "Polnoc": {
        "slug": "Polnoc",
        "zones": [f"Rybnik-Północ {i}" for i in range(1, 6)],
    },
    "Radziejow / Popielow": {
        "slug": "Radziejow__Popielow",
        "zones": [
            "Radziejów",
            "Popielów 1",
            "Popielów 2",
            "Popielów 3",
        ],
    },
    "Smolna / Zamyslow / Meksyk": {
        "slug": "Smolna__Zamyslow__Meksyk",
        "zones": [
            "Smolna 1",
            "Smolna 2",
            "Zamysłów 1",
            "Zamysłów 2",
            "Zamysłów 3",
            "Meksyk",
        ],
    },
    "Srodmiescie / Wielopole / Kuznia": {
        "slug": "Srodmiescie__Wielopole__Kuznia",
        "zones": [
            "Śródmieście 1",
            "Śródmieście 2",
            "Wielopole 1",
            "Wielopole 2",
            "Kuźnia Rybnicka",
        ],
        # Page-2 footer abbreviates "Kuźnia Rybnicka" to just "Kuźnia".
        "zone_aliases": {"Kuźnia Rybnicka": ["Kuźnia"]},
    },
    "Zebrzydowice": {
        "slug": "Zebrzydowice",
        "zones": [f"Zebrzydowice {i}" for i in range(1, 5)],
    },
}

PROPERTY_TYPES = ("residential", "commercial")

# Maps PDF waste-type token → (friendly English name, MDI icon)
WASTE_TYPE_MAP: dict[str, tuple[str, str]] = {
    "ZMIESZANE": ("Mixed waste", "mdi:trash-can"),
    "SEGREGOWANE": ("Recyclables", "mdi:recycle"),
    "BIODEGRADOWALNE": ("Bio / organic", "mdi:leaf"),
    "POPIOŁY/ŻUŻEL": ("Ash", "mdi:fireplace"),
    "GABARYTY": ("Bulky waste", "mdi:sofa"),
}

TEST_CASES = {
    "Paruszowiec-Piaski residential": {
        "district": "Paruszowiec / Kamien",
        "sub_district": "Paruszowiec-Piaski",
        "property_type": "residential",
    },
    "Boguszowice Stare residential (all sub-districts)": {
        "district": "Boguszowice Stare",
        "property_type": "residential",
    },
    "Niedobczyce commercial": {
        "district": "Niedobczyce",
        "property_type": "commercial",
    },
    "Zebrzydowice 1 residential": {
        "district": "Zebrzydowice",
        "sub_district": "Zebrzydowice 1",
        "property_type": "residential",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Download the current schedule PDF for your district from the "
        "Rybnik city website: https://www.rybnik.eu/dla-mieszkancow/odpady-komunalne/ "
        "(navigate to the current year's schedules). "
        "Open page 1 of the PDF and find your Rejon (sub-district zone) name "
        "in the left column of the table."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "district": (
            "The district / area group name (determines which PDF is downloaded). "
            f"Must be one of: {', '.join(DISTRICT_MAP.keys())}."
        ),
        "sub_district": (
            "The Rejon (zone) name as shown in the left column of the PDF cover-page table "
            "(e.g. 'Zebrzydowice 1', 'Paruszowiec-Piaski', 'Kamień 1'). "
            "Leave blank to return all zones in the district."
        ),
        "property_type": (
            "Type of property. One of: 'residential' (zamieszkałe, default), "
            "'commercial' (firmy/niezamieszkałe)."
        ),
    },
}

# Matches a waste-type row: keyword followed by exactly 12 month columns of digits/semicolons.
# ZMIESZANE / SEGREGOWANE / BIODEGRADOWALNE always carry 12 columns; POPIOŁY/ŻUŻEL is included
# so we can skip it cleanly when grouping rows into per-zone blocks (it can contain '-' dashes
# for summer months and is not currently returned as a Collection).
# GABARYTY is read separately from the page-2 footer (see _extract_gabaryty_map).
_ROW_RE = re.compile(
    r"(ZMIESZANE|SEGREGOWANE|BIODEGRADOWALNE|POPIOŁY/ŻUŻEL)"
    r"((?:\s+(?:[\d;]+|-)){12})"
)

_DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4})")


def _normalize_rejon(name: str) -> str:
    """Normalize a Rejon name for fuzzy comparison.

    Strips whitespace, hyphens, and underscores, then casefolds.
    Handles pypdf occasionally omitting hyphens from merged cells
    (e.g. 'ParuszowiecPiaski' matches 'Paruszowiec-Piaski').
    """
    normalized = unicodedata.normalize("NFC", name)
    return re.sub(r"[\s\-_]+", "", normalized).casefold()


def _make_zone_regex(name: str) -> re.Pattern:
    """Build a regex that matches `name` allowing flexible whitespace.

    Internal spaces match any whitespace run (including newlines), so a zone
    name that pypdf splits across two lines (e.g. "Boguszowice Stare\\n1")
    still matches. The lookbehind rejects letter prefixes (so "Niedobczyce"
    doesn't match inside "ABCNiedobczyce") but allows digit prefixes (so
    matching survives concatenations like "27.07.2026Niedobczyce 7"). The
    lookahead rejects trailing digits (so "Smolna 1" doesn't match
    "Smolna 14").
    """
    escaped = re.escape(name)
    # Allow hyphen to be followed by optional whitespace (handles
    # "Paruszowiec- Piaski" produced by pypdf for wrapped cells).
    escaped = escaped.replace(r"\-", r"-\s*")
    # Treat any run of escaped spaces as flexible whitespace.
    escaped = re.sub(r"\\\ +", lambda _m: r"\s+", escaped)
    return re.compile(r"(?<![A-Za-z])" + escaped + r"(?!\d)", re.IGNORECASE)


def _find_cover_page_text(reader: PdfReader) -> str:
    """Return the text of the first page that contains the Rejon table header."""
    for page in reader.pages:
        text = page.extract_text() or ""
        if "Rejony" in text and "Nazwy" in text:
            return text
    return ""


def _find_schedule_page_text(reader: PdfReader) -> str:
    """Return text from the first page that contains 'ZMIESZANE'."""
    for page in reader.pages:
        text = page.extract_text() or ""
        if "ZMIESZANE" in text:
            return text
    raise ValueError(
        "Could not find the schedule table in the PDF "
        "(no page contains 'ZMIESZANE'). The PDF format may have changed."
    )


def _extract_rejon_order(cover_text: str, expected_zones: list[str]) -> list[str]:
    """Return the cover-page zones in the order they appear on page 1.

    Uses the district-specific `expected_zones` list as a search index, since the
    cover-page text often wraps zone names across lines or interleaves them with
    long street-name lists. The returned list preserves the order of first
    occurrence in the cover text.
    """
    if not cover_text:
        return []

    # Restrict search to the area after the "Rejony Nazwy ulic" header
    # (some footer markers contain similar words).
    header_idx = cover_text.find("Rejony")
    haystack = cover_text[header_idx:] if header_idx >= 0 else cover_text

    matches: list[tuple[int, str]] = []
    for zone in expected_zones:
        rx = _make_zone_regex(zone)
        m = rx.search(haystack)
        if m:
            matches.append((m.start(), zone))

    matches.sort()
    return [name for _, name in matches]


def _extract_blocks(text: str) -> list[list[tuple[str, list[str]]]]:
    """Extract data blocks (groups of waste-type rows) from the schedule page text.

    Each block always starts with ZMIESZANE. POPIOŁY/ŻUŻEL is optional (residential
    only). The block always includes a SEGREGOWANE and a BIODEGRADOWALNE row in that
    sequence. POPIOŁY rows are currently dropped (the project does not yet surface an
    "ash" waste type), but recognising them is required so the parser can keep its
    block boundaries straight.
    """
    all_rows: list[tuple[str, list[str]]] = []

    for m in _ROW_RE.finditer(text):
        waste_key = m.group(1)
        month_tokens = m.group(2).split()
        if len(month_tokens) != 12:
            _LOGGER.warning(
                "Expected 12 month columns for %s, got %d — skipping row.",
                waste_key,
                len(month_tokens),
            )
            continue
        all_rows.append((waste_key, month_tokens))

    if not all_rows:
        raise ValueError(
            "No waste-type rows found in PDF text. The PDF format may have changed."
        )

    # A block starts at each ZMIESZANE row. Slice between ZMIESZANE markers.
    block_starts = [i for i, (k, _) in enumerate(all_rows) if k == "ZMIESZANE"]
    if not block_starts:
        raise ValueError(
            "No complete schedule blocks found in PDF text. "
            "The PDF format may have changed."
        )

    blocks: list[list[tuple[str, list[str]]]] = []
    for idx, start in enumerate(block_starts):
        end = block_starts[idx + 1] if idx + 1 < len(block_starts) else len(all_rows)
        blocks.append(all_rows[start:end])

    return blocks


def _extract_gabaryty_map(
    schedule_text: str, zones: list[str], zone_aliases: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Parse the Gabaryty (bulky waste) section that follows the schedule table.

    The page-2 footer lists each Rejon zone alongside two pickup dates per year. It
    is rendered as a 2-column table whose text-extraction order is unreliable (zones
    and dates can appear in any order, sometimes flanking each other). The algorithm
    groups consecutive same-type tokens into "runs" and pairs each zones-run with
    its flanking dates-runs positionally:
      - Leading dates-run (immediately before a zones-run) fills the first zones
        in that run, two dates per zone.
      - Trailing dates-run (immediately after) fills any remaining zones.
    Unused dates from a leading run carry over to the next zones-run, so the same
    pool of dates can serve multiple consecutive zones-runs.

    Returns a dict mapping the canonical zone name to a list of date strings
    ("DD.MM.YYYY"). Zones with no Gabaryty info simply don't appear in the map.
    """
    last_bio = schedule_text.rfind("BIODEGRADOWALNE")
    if last_bio < 0:
        return {}
    eol = schedule_text.find("\n", last_bio)
    footer = schedule_text[eol if eol >= 0 else last_bio :]
    # Collapse all whitespace to single spaces — makes multi-line zone names match.
    flat = re.sub(r"\s+", " ", footer).strip()
    if not flat:
        return {}

    # Build the list of (kind, value, pos) tokens.
    tokens: list[tuple[str, object, int]] = []
    for m in _DATE_RE.finditer(flat):
        tokens.append(("date", m.group(1), m.start()))

    # Build an alias-aware lookup: each searchable string maps back to its canonical zone.
    alias_to_canonical: dict[str, str] = {}
    for zone in zones:
        alias_to_canonical[zone] = zone
        for alias in zone_aliases.get(zone, []):
            alias_to_canonical[alias] = zone

    # Prefer matching longer aliases first so we don't shadow ("Kuźnia Rybnicka" before "Kuźnia").
    seen_canonical: set[str] = set()
    for alias in sorted(alias_to_canonical.keys(), key=len, reverse=True):
        canonical = alias_to_canonical[alias]
        if canonical in seen_canonical:
            continue
        rx = _make_zone_regex(alias)
        m = rx.search(flat)
        if m:
            tokens.append(("zone", canonical, m.start()))
            seen_canonical.add(canonical)

    tokens.sort(key=lambda t: t[2])
    if not tokens:
        return {}

    # Group consecutive same-kind tokens into runs.
    runs: list[list[tuple[str, object, int]]] = []
    current = [tokens[0]]
    for t in tokens[1:]:
        if t[0] == current[-1][0]:
            current.append(t)
        else:
            runs.append(current)
            current = [t]
    runs.append(current)

    # Mutable pool of remaining dates per dates-run, indexed by run position.
    run_dates: dict[int, list[str]] = {
        i: [t[1] for t in r] for i, r in enumerate(runs) if r[0][0] == "date"
    }

    result: dict[str, list[str]] = {}
    for run_idx, run in enumerate(runs):
        if run[0][0] != "zone":
            continue
        leading_idx = (
            run_idx - 1 if run_idx > 0 and (run_idx - 1) in run_dates else None
        )
        trailing_idx = (
            run_idx + 1
            if run_idx + 1 < len(runs) and (run_idx + 1) in run_dates
            else None
        )
        leading = run_dates.get(leading_idx, []) if leading_idx is not None else []
        trailing = run_dates.get(trailing_idx, []) if trailing_idx is not None else []

        n_leading_pairs = min(len(leading) // 2, len(run))
        for k in range(n_leading_pairs):
            canonical = run[k][1]
            result[canonical] = [leading[k * 2], leading[k * 2 + 1]]
        if leading_idx is not None:
            run_dates[leading_idx] = leading[n_leading_pairs * 2 :]

        remaining = run[n_leading_pairs:]
        n_trailing_pairs = min(len(trailing) // 2, len(remaining))
        for k in range(n_trailing_pairs):
            canonical = remaining[k][1]
            result[canonical] = [trailing[k * 2], trailing[k * 2 + 1]]
        if trailing_idx is not None:
            run_dates[trailing_idx] = trailing[n_trailing_pairs * 2 :]

    return result


def _build_entries(
    blocks: list[list[tuple[str, list[str]]]],
    rejon_order: list[str],
    gabaryty_map: dict[str, list[str]],
    year: int,
    sub_district_filter: str,
) -> list[Collection]:
    """Build Collection entries, optionally filtered by sub_district."""
    entries: list[Collection] = []
    matched_filter = False

    for block_idx, block in enumerate(blocks):
        rejon_name = (
            rejon_order[block_idx]
            if block_idx < len(rejon_order)
            else f"Zone {block_idx + 1}"
        )

        if sub_district_filter:
            if _normalize_rejon(sub_district_filter) != _normalize_rejon(rejon_name):
                continue
            matched_filter = True

        for waste_key, month_tokens in block:
            if waste_key not in WASTE_TYPE_MAP:
                continue
            # POPIOŁY/ŻUŻEL (ash) is parsed but not surfaced as a Collection — its
            # dashes-for-summer-months format is currently noise in HA calendars.
            if waste_key == "POPIOŁY/ŻUŻEL":
                continue
            friendly_name, icon = WASTE_TYPE_MAP[waste_key]
            for month_idx, token in enumerate(month_tokens):
                month_num = month_idx + 1
                for day_str in token.split(";"):
                    day_str = day_str.strip()
                    if not day_str.isdigit():
                        continue
                    try:
                        collection_date = date(year, month_num, int(day_str))
                    except ValueError:
                        _LOGGER.warning(
                            "Invalid date %d-%02d-%s — skipping.",
                            year,
                            month_num,
                            day_str,
                        )
                        continue
                    entries.append(
                        Collection(date=collection_date, t=friendly_name, icon=icon)
                    )

        # Add Gabaryty (bulky waste) dates for this Rejon, if any.
        for date_str in gabaryty_map.get(rejon_name, []):
            try:
                day, month, yr = (int(x) for x in date_str.split("."))
                collection_date = date(yr, month, day)
            except ValueError:
                _LOGGER.warning(
                    "Invalid Gabaryty date %r for %s — skipping.", date_str, rejon_name
                )
                continue
            friendly_name, icon = WASTE_TYPE_MAP["GABARYTY"]
            entries.append(Collection(date=collection_date, t=friendly_name, icon=icon))

    if sub_district_filter and not matched_filter:
        raise SourceArgumentNotFoundWithSuggestions(
            "sub_district", sub_district_filter, rejon_order
        )

    if not entries:
        raise ValueError("No collection entries could be parsed from the PDF.")

    return entries


class Source:
    def __init__(
        self,
        district: str = "",
        sub_district: str = "",
        property_type: str = "residential",
    ):
        self._property_type = property_type.lower().strip()
        if self._property_type not in PROPERTY_TYPES:
            raise SourceArgumentNotFoundWithSuggestions(
                "property_type", property_type, list(PROPERTY_TYPES)
            )

        self._sub_district = sub_district.strip()

        district = district.strip()
        if not district:
            raise SourceArgumentRequiredWithSuggestions(
                "district",
                "district is required",
                list(DISTRICT_MAP.keys()),
            )
        if district not in DISTRICT_MAP:
            raise SourceArgumentNotFoundWithSuggestions(
                "district", district, list(DISTRICT_MAP.keys())
            )
        self._district = district
        cfg = DISTRICT_MAP[district]
        self._slug = cfg["slug"]
        self._expected_zones: list[str] = cfg["zones"]
        self._zone_aliases: dict[str, list[str]] = cfg.get("zone_aliases", {})

    def fetch(self) -> list[Collection]:
        year = datetime.now().year
        pdf_bytes, actual_year = self._fetch_pdf(year)

        reader = PdfReader(BytesIO(pdf_bytes))
        cover_text = _find_cover_page_text(reader)
        schedule_text = _find_schedule_page_text(reader)

        rejon_order = _extract_rejon_order(cover_text, self._expected_zones)
        if not rejon_order:
            # Fall back to the declared zone list if cover parsing fails — the
            # page-2 schedule blocks themselves are still in cover-page order.
            _LOGGER.warning(
                "Cover-page Rejon extraction failed for %s — falling back to "
                "the declared zone list.",
                self._district,
            )
            rejon_order = list(self._expected_zones)

        blocks = _extract_blocks(schedule_text)
        gabaryty_map = _extract_gabaryty_map(
            schedule_text, self._expected_zones, self._zone_aliases
        )

        _LOGGER.debug(
            "District '%s': %d blocks, %d Rejon names: %s; gabaryty zones: %s",
            self._district,
            len(blocks),
            len(rejon_order),
            rejon_order,
            list(gabaryty_map.keys()),
        )

        return _build_entries(
            blocks, rejon_order, gabaryty_map, actual_year, self._sub_district
        )

    def _build_url(self, year: int) -> str:
        base = _BASE_URL.format(year=year)
        if self._property_type == "commercial":
            return f"{base}Firmy{year}_{self._slug}_firmy_{year}.pdf"
        # residential (default)
        return f"{base}zamieszkale{year}_{self._slug}_{year}.pdf"

    def _fetch_pdf(self, year: int) -> tuple[bytes, int]:
        """Download the schedule PDF, trying current year then year-1 on HTTP 404.

        Returns (pdf_bytes, year_used).
        """
        for attempt_year in (year, year - 1):
            url = self._build_url(attempt_year)
            _LOGGER.debug("Fetching waste schedule PDF: %s", url)
            resp = requests.get(url, timeout=30)
            if resp.status_code == 404:
                if attempt_year == year:
                    _LOGGER.info(
                        "PDF for year %d not found (HTTP 404), trying %d.",
                        attempt_year,
                        attempt_year - 1,
                    )
                else:
                    _LOGGER.info(
                        "PDF for year %d not found (HTTP 404).",
                        attempt_year,
                    )
                continue
            resp.raise_for_status()
            return resp.content, attempt_year

        raise FileNotFoundError(
            f"Could not fetch Rybnik waste schedule PDF for {year} or {year - 1}. "
            f"Last URL tried: {self._build_url(year - 1)}"
        )
