"""Source for SMOLO a.s. (Třinec), Czech Republic."""

from __future__ import annotations

import itertools
import logging
import re
import unicodedata
import urllib.parse
from dataclasses import dataclass, field
from datetime import date, timedelta
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

_LOGGER = logging.getLogger(__name__)

TITLE = "SMOLO a.s. (Třinec)"
DESCRIPTION = (
    "Source for SMOLO a.s. household waste collection schedule for the town "
    "of Třinec, Czech Republic."
)
URL = "https://www.smolo.cz/sluzby/odpadove-hospodarstvi/informace-pro-domacnosti/"
COUNTRY = "cz"

SOURCE_CODEOWNERS = ["@jan-tdy"]

_LANDING_PAGE_URL = (
    "https://www.smolo.cz/sluzby/odpadove-hospodarstvi/informace-pro-domacnosti/"
)

_WEEKDAY_TOKENS = {"PO": 0, "ÚT": 1, "ST": 2, "ČT": 3, "PÁ": 4}  # Monday=0 .. Friday=4

_SKO_T = "Směsný komunální odpad"
_BIO_T = "Biologický odpad"
_SEP_T = "Tříděný odpad (pytle/240L nádoby)"
_SEP_YELLOW_T = "Tříděný odpad - plast (žluté pytle/nádoby)"
_SEP_BLUE_T = "Tříděný odpad - papír (modré pytle/nádoby)"

ICON_MAP = {
    _SKO_T: Icons.GENERAL_WASTE,
    _BIO_T: Icons.ORGANIC,
    _SEP_T: Icons.RECYCLING,
    _SEP_YELLOW_T: Icons.RECYCLING,
    _SEP_BLUE_T: Icons.PAPER,
}

TEST_CASES = {
    "Nebory": {"district": "Nebory"},
    "Karpentná": {"district": "Karpentná"},
    "Stare Mesto Husova": {"district": "Staré Město", "street": "Husova"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open the SMOLO a.s. household-waste page "
        "(https://www.smolo.cz/sluzby/odpadove-hospodarstvi/informace-pro-domacnosti/) "
        "and look up the current 'Třinec – harmonogram' PDF for the SKO/BIO/SEP "
        "schedule. Use the 'ČÁST MĚSTA' (part of town / district) column value "
        "as the 'district' argument, e.g. 'Staré Město', 'Lyžbice', 'Nebory', "
        "'Karpentná'. If your district appears multiple times in the table "
        "with different street lists, also set 'street' to one street name "
        "from the 'LOKALITA' column to disambiguate."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "district": "District (část města)",
        "street": "Street (optional, for disambiguation)",
    },
}
PARAM_DESCRIPTIONS = {
    "en": {
        "district": (
            "The town district / part of town ('část města') exactly as it "
            "appears in the SMOLO Třinec collection schedule, e.g. 'Staré "
            "Město', 'Lyžbice', 'Nebory', 'Karpentná'."
        ),
        "street": (
            "Optional street name used to disambiguate districts that appear "
            "on multiple rows of the schedule with different street lists "
            "(e.g. 'Staré Město', 'Oldřichovice', 'Lyžbice')."
        ),
    },
}


def _normalize(text: str) -> str:
    """Lowercase and strip diacritics for tolerant matching."""
    normalized = unicodedata.normalize("NFKD", text)
    without_diacritics = "".join(c for c in normalized if not unicodedata.combining(c))
    return without_diacritics.lower().strip()


def _fields_of(line: str) -> list[tuple]:
    """Split a layout-mode-extracted line into (start_col, text) fields,
    where fields are separated by runs of 2+ spaces."""
    return [(m.start(), m.group()) for m in re.finditer(r"\S(?:[^\s]|\s(?!\s))*", line)]


def _find_split_column(starts: list[int]) -> int:
    """Find the largest gap in a sorted list of column-start positions to
    split fields into a 'district' cluster and a 'street' cluster."""
    unique_starts = sorted(set(starts))
    if len(unique_starts) < 2:
        return (unique_starts[0] + 1) if unique_starts else 20
    best_gap = -1
    split_col = unique_starts[0] + 1
    for a, b in itertools.pairwise(unique_starts):
        if b - a > best_gap:
            best_gap = b - a
            split_col = (a + b) // 2
    return split_col


@dataclass
class _Page1Row:
    weekday: int
    district_raw: str
    streets: list[str] = field(default_factory=list)

    @property
    def bio_on_monday(self) -> bool:
        return "bio*" in _normalize(self.district_raw)

    @property
    def district_names(self) -> list[str]:
        # Strip any "(...)" annotation, then split on commas for
        # multi-district cells like "Terasa, Lyžbice Ves".
        cleaned = re.sub(r"\(.*?\)", "", self.district_raw)
        return [p.strip() for p in cleaned.split(",") if p.strip()]

    @property
    def street_text(self) -> str:
        return " ".join(self.streets)


def _parse_page1(text: str) -> tuple:
    """Parse the SKO/BIO page (page 1) of the schedule PDF.

    Returns (rows, prose_lines).
    """
    lines = list(text.split("\n"))
    header_idx = next(
        (
            i
            for i, line_ in enumerate(lines)
            if "ČÁST MĚSTA" in line_ and "LOKALITA" in line_
        ),
        None,
    )
    if header_idx is None:
        return [], []

    # The header wraps ("SVOZOVÝ" / "DEN"); the table body starts two lines down.
    body_start = header_idx + 2

    body_end = len(lines)
    for i in range(body_start, len(lines)):
        if lines[i] and not lines[i][0].isspace():
            body_end = i
            break

    body_lines = lines[body_start:body_end]

    non_weekday_starts = [
        s
        for line_ in body_lines
        for s, t in _fields_of(line_)
        if t not in _WEEKDAY_TOKENS
    ]
    split_col = _find_split_column(non_weekday_starts)

    # Pre-scan for the first weekday token: it may appear visually mid-block
    # (vertically centered within its block of rows) rather than on the very
    # first row of that block, but the first block in the table always starts
    # at the top regardless of where its token lands.
    current_weekday = None
    for line_ in body_lines:
        for _, t in _fields_of(line_):
            if t in _WEEKDAY_TOKENS:
                current_weekday = _WEEKDAY_TOKENS[t]
                break
        if current_weekday is not None:
            break

    rows: list[_Page1Row] = []
    open_row: _Page1Row | None = None
    pending_before: list[str] = []

    for line_ in body_lines:
        dist_field = None
        street_fields = []
        for s, t in _fields_of(line_):
            if t in _WEEKDAY_TOKENS:
                current_weekday = _WEEKDAY_TOKENS[t]
                continue
            if s < split_col:
                dist_field = t
            else:
                street_fields.append(t)
        street_text = ", ".join(street_fields)

        if dist_field and not dist_field.startswith("("):
            row = _Page1Row(
                weekday=current_weekday if current_weekday is not None else 0,
                district_raw=dist_field,
                streets=list(pending_before),
            )
            pending_before = []
            if street_text:
                row.streets.append(street_text)
            rows.append(row)
            open_row = row
        elif dist_field and dist_field.startswith("("):
            # continuation of the open row's district annotation, e.g.
            # "(BIO* svoz v pondělí)" wrapping onto its own line
            if open_row is not None:
                open_row.district_raw += " " + dist_field
                if street_text:
                    open_row.streets.append(street_text)
            elif street_text:
                pending_before.append(street_text)
        else:
            if street_text:
                if open_row is not None:
                    open_row.streets.append(street_text)
                else:
                    pending_before.append(street_text)

    return rows, lines[body_end:]


_DATE_FIELD_RE = re.compile(r"\d{1,2}[.,]\d{1,2}\.?")
_WD_FIELD_RE = re.compile(r"^(PO|ÚT|ST|ČT|PÁ)(?:\s?(\d.*))?$")


@dataclass
class _Page2Block:
    weekday: int
    dates: list[str]
    text: list[str]

    @property
    def joined_text(self) -> str:
        return " ".join(self.text)


def _parse_page2(text: str) -> list[_Page2Block]:
    """Parse the SEP (sorted waste) page (page 2) of the schedule PDF."""
    lines = list(text.split("\n"))
    header_idx = next(
        (i for i, line_ in enumerate(lines) if "Část" in line_ and "lokality" in line_),
        None,
    )
    if header_idx is None:
        return []

    # The header wraps onto a continuation line; skip to the first blank line.
    body_start = header_idx + 1
    while body_start < len(lines) and lines[body_start].strip():
        body_start += 1

    blocks: list[_Page2Block] = []
    cur_text: list[str] = []
    cur_weekday: int | None = None
    cur_dates: list[str] = []

    def flush() -> None:
        nonlocal cur_text, cur_weekday, cur_dates
        if cur_weekday is not None and cur_text:
            blocks.append(
                _Page2Block(
                    weekday=cur_weekday, dates=list(cur_dates), text=list(cur_text)
                )
            )
        cur_text, cur_weekday, cur_dates = [], None, []

    for line_ in lines[body_start:]:
        if not line_.strip():
            if cur_weekday is not None:
                flush()
            continue

        line_text: list[str] = []
        line_weekday: int | None = None
        line_dates: list[str] = []
        for _, tok in _fields_of(line_):
            m = _WD_FIELD_RE.match(tok)
            if m:
                line_weekday = _WEEKDAY_TOKENS[m.group(1)]
                if m.group(2):
                    line_dates.extend(_DATE_FIELD_RE.findall(m.group(2)))
                continue
            if re.fullmatch(r"[\d.,\s]+", tok):
                found = _DATE_FIELD_RE.findall(tok)
                if found:
                    line_dates.extend(found)
                    continue
            line_text.append(tok)

        if line_weekday is not None and cur_weekday is not None:
            flush()

        cur_text.extend(line_text)
        if line_weekday is not None:
            cur_weekday = line_weekday
        cur_dates.extend(line_dates)

    flush()
    return blocks


_PLATNY_OD_RE = re.compile(r"PLATN[ÝY]\s+OD\s+(\d{1,2})\.(\d{1,2})\.(\d{4})")
_HOLIDAY_SHIFT_RE = re.compile(
    r"(\d{1,2}\.\d{1,2}\.\d{4})\s*\(svoz se\s*posouvá na \S+\s+(\d{1,2}\.\d{1,2}\.\d{4})\)"
)
_BIO_WEEKS_RE = re.compile(r"\(([\d.,\s]+)týden roku (\d{4})\)")


def _parse_year(text: str) -> int | None:
    m = _PLATNY_OD_RE.search(text)
    if m:
        return int(m.group(3))
    return None


def _parse_date_ddmmyyyy(text: str) -> date | None:
    parts = text.split(".")
    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def _parse_holiday_shifts(prose_lines: list[str]) -> dict:
    joined = " ".join(prose_lines)
    shifts = {}
    for m in _HOLIDAY_SHIFT_RE.finditer(joined):
        from_date = _parse_date_ddmmyyyy(m.group(1))
        to_date = _parse_date_ddmmyyyy(m.group(2))
        if from_date and to_date:
            shifts[from_date] = to_date
    if not shifts:
        _LOGGER.warning(
            "smolo_cz: could not parse holiday-shift sentence from the SKO/BIO "
            "PDF text; holiday shifts will not be applied this run."
        )
    return shifts


def _parse_sparse_bio_weeks(prose_lines: list[str]) -> set | None:
    joined = " ".join(prose_lines)
    m = _BIO_WEEKS_RE.search(joined)
    if not m:
        _LOGGER.warning(
            "smolo_cz: could not parse the 'BIO 1x/month in Jan/Feb/Dec' week "
            "numbers from the PDF text; falling back to 'every even week in "
            "those months' as a simplification."
        )
        return None
    weeks = set()
    for chunk in m.group(1).split(","):
        chunk = chunk.strip().rstrip(".")
        if chunk.isdigit():
            weeks.add(int(chunk))
    return weeks or None


def _iter_year_dates(year: int):
    d = date(year, 1, 1)
    end = date(year, 12, 31)
    while d <= end:
        yield d
        d += timedelta(days=1)


class Source:
    def __init__(self, district: str, street: str = "") -> None:
        self._district = district
        self._street = street

    def _fetch_pdf_url(self, session: requests.Session) -> str:
        response = session.get(_LANDING_PAGE_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if ".pdf" not in href.lower():
                continue
            link_descriptor = _normalize(f"{a.get_text(' ', strip=True)} {href}")
            if "trinec" in link_descriptor and all(
                token in link_descriptor for token in ("sko", "bio", "sep")
            ):
                return urllib.parse.urljoin(_LANDING_PAGE_URL, href)

        raise SourceArgumentNotFoundWithSuggestions(
            "district",
            self._district,
            [
                "Could not locate the Třinec SKO/BIO/SEP schedule PDF link on "
                "the SMOLO household-waste page. The page layout may have "
                "changed."
            ],
        )

    def _match_page1_rows(self, rows: list[_Page1Row]) -> list[_Page1Row]:
        target_district = _normalize(self._district)
        target_street = _normalize(self._street) if self._street else ""

        district_matches = [
            row
            for row in rows
            if any(_normalize(n) == target_district for n in row.district_names)
        ]

        if not district_matches:
            all_names = sorted({n for row in rows for n in row.district_names})
            raise SourceArgumentNotFoundWithSuggestions(
                "district", self._district, all_names
            )

        if len(district_matches) == 1:
            return district_matches

        if target_street:
            street_matches = [
                row
                for row in district_matches
                if target_street in _normalize(row.street_text)
            ]
            if len(street_matches) == 1:
                return street_matches
            if street_matches:
                # multiple rows still match (unlikely) -- return them all
                return street_matches

        suggestions = [
            f"{row.district_raw} ({row.street_text})" for row in district_matches
        ]
        raise SourceArgumentNotFoundWithSuggestions(
            "street" if target_street else "district",
            self._street if target_street else self._district,
            suggestions,
        )

    def _match_page2_blocks(self, blocks: list[_Page2Block]) -> list[_Page2Block]:
        target_district = _normalize(self._district)
        matches = [
            block
            for block in blocks
            if target_district in _normalize(block.joined_text)
        ]
        # The Nebory yellow/plastic (žlutá) and blue/paper (modrá) rows only
        # mention "Nebory" once (vertically centered between the two rows in
        # the source PDF); attach both explicitly when the district is Nebory.
        if target_district == "nebory":
            for block in blocks:
                text_norm = _normalize(block.joined_text)
                if (
                    "nadoba" in text_norm or "pytle" in text_norm
                ) and block not in matches:
                    if "zluta" in text_norm or "modra" in text_norm:
                        matches.append(block)
        return matches

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; HomeAssistant)"}
        )

        pdf_url = self._fetch_pdf_url(session)
        pdf_response = session.get(pdf_url, timeout=30)
        pdf_response.raise_for_status()

        reader = PdfReader(BytesIO(pdf_response.content))
        page1_text = reader.pages[0].extract_text(extraction_mode="layout") or ""
        page2_text = (
            reader.pages[1].extract_text(extraction_mode="layout")
            if len(reader.pages) > 1
            else ""
        ) or ""

        rows, prose_lines = _parse_page1(page1_text)
        if not rows:
            raise SourceArgumentNotFoundWithSuggestions(
                "district",
                self._district,
                ["Could not parse the SKO/BIO schedule table from the PDF."],
            )

        year = _parse_year(page1_text) or date.today().year
        holiday_shifts = _parse_holiday_shifts(prose_lines)
        sparse_bio_weeks = _parse_sparse_bio_weeks(prose_lines)

        matched_rows = self._match_page1_rows(rows)

        entries: list[Collection] = []

        for row in matched_rows:
            bio_weekday = 0 if row.bio_on_monday else row.weekday

            for d in _iter_year_dates(year):
                iso_week = d.isocalendar()[1]
                is_odd_week = iso_week % 2 == 1

                if d.weekday() == row.weekday and is_odd_week:
                    final_date = holiday_shifts.get(d, d)
                    entries.append(
                        Collection(date=final_date, t=_SKO_T, icon=ICON_MAP[_SKO_T])
                    )

                if d.weekday() == bio_weekday and not is_odd_week:
                    if d.month in (1, 2, 12):
                        if sparse_bio_weeks is not None:
                            if iso_week not in sparse_bio_weeks:
                                continue
                        # else: fall back to "every even week" simplification
                    final_date = holiday_shifts.get(d, d)
                    entries.append(
                        Collection(date=final_date, t=_BIO_T, icon=ICON_MAP[_BIO_T])
                    )

        # SEP (sorted waste) — page 2, explicit date lists.
        page2_blocks = _parse_page2(page2_text)
        page2_year = _parse_year(page2_text) or year
        matched_blocks = self._match_page2_blocks(page2_blocks)

        for block in matched_blocks:
            text_norm = _normalize(block.joined_text)
            if "zluta" in text_norm:
                sep_t = _SEP_YELLOW_T
            elif "modra" in text_norm:
                sep_t = _SEP_BLUE_T
            else:
                sep_t = _SEP_T

            for raw_date in block.dates:
                parts = re.split(r"[.,]", raw_date)
                parts = [p for p in parts if p]
                if len(parts) < 2:
                    _LOGGER.warning(
                        "smolo_cz: skipping unparsable SEP date fragment %r", raw_date
                    )
                    continue
                try:
                    day, month = int(parts[0]), int(parts[1])
                    d = date(page2_year, month, day)
                except ValueError:
                    _LOGGER.warning(
                        "smolo_cz: skipping unparsable SEP date fragment %r", raw_date
                    )
                    continue
                entries.append(Collection(date=d, t=sep_t, icon=ICON_MAP[sep_t]))

        return entries
