"""Pipeline components for the SMOLO a.s. (Třinec) waste schedule PDF.

SMOLO publishes one two-page PDF a year for the town:

* page 1 is a table of town districts ("ČÁST MĚSTA") with a weekday ("SVOZOVÝ
  DEN") and the streets served. Residual waste is collected on that weekday in
  odd ISO weeks, organic waste in even ones (rows marked "BIO* svoz v pondělí"
  on Monday). A sentence under the table lists holiday shifts and the weeks of
  the once-a-month organic rounds in January, February and December.
* page 2 lists the sorted-waste (bags and 240 L bins) rounds as explicit dates
  per group of districts, with separate yellow (plastic) and blue (paper) rows
  for Nebory.

The text layer only survives as a table in pypdf's layout mode, so
:class:`SmoloScheduleParser` reads both pages that way and
:class:`SmoloScheduleExpander` turns the configured district (and optionally
street) into ``(date, label)`` rows for an ``ICSTransformer``. The text
helpers are pure and work on plain strings, so they can be tested without a PDF.
"""

from __future__ import annotations

import itertools
import logging
import re
import unicodedata
from datetime import date, timedelta
from typing import TYPE_CHECKING, NamedTuple

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from requests import Response

    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

RESIDUAL = "Směsný komunální odpad"
ORGANIC = "Biologický odpad"
SORTED = "Tříděný odpad (pytle/240L nádoby)"
SORTED_YELLOW = "Tříděný odpad - plast (žluté pytle/nádoby)"
SORTED_BLUE = "Tříděný odpad - papír (modré pytle/nádoby)"

_WEEKDAY_TOKENS = {"PO": 0, "ÚT": 1, "ST": 2, "ČT": 3, "PÁ": 4}  # Monday=0

_DATE_FIELD_RE = re.compile(r"\d{1,2}[.,]\d{1,2}\.?")
_WD_FIELD_RE = re.compile(r"^(PO|ÚT|ST|ČT|PÁ)(?:\s?(\d.*))?$")
_VALID_FROM_RE = re.compile(r"PLATN[ÝY]\s+OD\s+(\d{1,2})\.(\d{1,2})\.(\d{4})")
_HOLIDAY_SHIFT_RE = re.compile(
    r"(\d{1,2}\.\d{1,2}\.\d{4})\s*\(svoz se\s*posouvá na \S+\s+(\d{1,2}\.\d{1,2}\.\d{4})\)"
)
_BIO_WEEKS_RE = re.compile(r"\(([\d.,\s]+)týden roku (\d{4})\)")


def normalize(text: str) -> str:
    """Lower-case and strip diacritics for tolerant matching."""
    decomposed = unicodedata.normalize("NFKD", text)
    return (
        "".join(c for c in decomposed if not unicodedata.combining(c)).lower().strip()
    )


def split_fields(line: str) -> list[tuple[int, str]]:
    """Split a layout-mode line into ``(start_column, text)`` fields.

    Fields are separated by runs of two or more spaces.
    """
    return [(m.start(), m.group()) for m in re.finditer(r"\S(?:[^\s]|\s(?!\s))*", line)]


def find_split_column(starts: list[int]) -> int:
    """The column splitting the "district" cluster from the "street" cluster.

    It sits in the middle of the largest gap between sorted field start columns.
    """
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


class DistrictRow(NamedTuple):
    """One row of the page-1 table."""

    weekday: int
    district_raw: str
    streets: tuple[str, ...]

    @property
    def bio_on_monday(self) -> bool:
        return "bio*" in normalize(self.district_raw)

    @property
    def district_names(self) -> list[str]:
        # Strip any "(...)" annotation, then split multi-district cells such as
        # "Terasa, Lyžbice Ves" on commas.
        cleaned = re.sub(r"\(.*?\)", "", self.district_raw)
        return [p.strip() for p in cleaned.split(",") if p.strip()]

    @property
    def street_text(self) -> str:
        return " ".join(self.streets)


class SortedBlock(NamedTuple):
    """One block of the page-2 table: a weekday, dates and the districts."""

    weekday: int
    dates: tuple[str, ...]
    text: tuple[str, ...]

    @property
    def joined_text(self) -> str:
        return " ".join(self.text)


class SmoloSchedule(NamedTuple):
    """Everything read from the PDF, before a district is chosen."""

    year: int
    rows: list[DistrictRow]
    holiday_shifts: dict[date, date]
    sparse_bio_weeks: set[int] | None
    blocks: list[SortedBlock]
    sorted_year: int


def parse_year(text: str) -> int | None:
    """The year of "PLATNÝ OD 01.01.2026", if printed."""
    match = _VALID_FROM_RE.search(text)
    return int(match.group(3)) if match else None


def _parse_date(text: str) -> date | None:
    parts = text.split(".")
    try:
        return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except (ValueError, IndexError):
        return None


def parse_district_table(text: str) -> tuple[list[DistrictRow], list[str]]:
    """Parse the residual/organic table (page 1).

    Returns the rows and the prose lines under the table.
    """
    lines = text.split("\n")
    header_idx = next(
        (
            i
            for i, line in enumerate(lines)
            if "ČÁST MĚSTA" in line and "LOKALITA" in line
        ),
        None,
    )
    if header_idx is None:
        return [], []

    # The header wraps ("SVOZOVÝ" / "DEN"); the body starts two lines down.
    body_start = header_idx + 2
    body_end = len(lines)
    for i in range(body_start, len(lines)):
        if lines[i] and not lines[i][0].isspace():
            body_end = i
            break
    body_lines = lines[body_start:body_end]

    split_col = find_split_column(
        [
            start
            for line in body_lines
            for start, token in split_fields(line)
            if token not in _WEEKDAY_TOKENS
        ]
    )

    # The first weekday token may sit mid-block (vertically centred), but the
    # first block of the table always starts at the top.
    current_weekday: int | None = None
    for line in body_lines:
        for _, token in split_fields(line):
            if token in _WEEKDAY_TOKENS:
                current_weekday = _WEEKDAY_TOKENS[token]
                break
        if current_weekday is not None:
            break

    # Each entry: [weekday, district_raw, streets]
    rows: list[list] = []
    open_row: list | None = None
    pending_before: list[str] = []

    for line in body_lines:
        district_field = None
        street_fields = []
        for start, token in split_fields(line):
            if token in _WEEKDAY_TOKENS:
                current_weekday = _WEEKDAY_TOKENS[token]
            elif start < split_col:
                district_field = token
            else:
                street_fields.append(token)
        street_text = ", ".join(street_fields)

        if district_field and not district_field.startswith("("):
            open_row = [
                current_weekday if current_weekday is not None else 0,
                district_field,
                list(pending_before),
            ]
            pending_before = []
            if street_text:
                open_row[2].append(street_text)
            rows.append(open_row)
        elif district_field:
            # "(BIO* svoz v pondělí)" wrapping onto a line of its own
            if open_row is not None:
                open_row[1] += " " + district_field
                if street_text:
                    open_row[2].append(street_text)
            elif street_text:
                pending_before.append(street_text)
        elif street_text:
            if open_row is not None:
                open_row[2].append(street_text)
            else:
                pending_before.append(street_text)

    return (
        [DistrictRow(w, d, tuple(s)) for w, d, s in rows],
        lines[body_end:],
    )


def parse_sorted_table(text: str) -> list[SortedBlock]:
    """Parse the sorted-waste table (page 2)."""
    lines = text.split("\n")
    header_idx = next(
        (i for i, line in enumerate(lines) if "Část" in line and "lokality" in line),
        None,
    )
    if header_idx is None:
        return []

    # The header wraps onto a continuation line; skip to the first blank line.
    body_start = header_idx + 1
    while body_start < len(lines) and lines[body_start].strip():
        body_start += 1

    blocks: list[SortedBlock] = []
    cur_text: list[str] = []
    cur_weekday: int | None = None
    cur_dates: list[str] = []

    def flush() -> None:
        nonlocal cur_text, cur_weekday, cur_dates
        if cur_weekday is not None and cur_text:
            blocks.append(SortedBlock(cur_weekday, tuple(cur_dates), tuple(cur_text)))
        cur_text, cur_weekday, cur_dates = [], None, []

    for line in lines[body_start:]:
        if not line.strip():
            if cur_weekday is not None:
                flush()
            continue

        line_text: list[str] = []
        line_weekday: int | None = None
        line_dates: list[str] = []
        for _, token in split_fields(line):
            match = _WD_FIELD_RE.match(token)
            if match:
                line_weekday = _WEEKDAY_TOKENS[match.group(1)]
                if match.group(2):
                    line_dates.extend(_DATE_FIELD_RE.findall(match.group(2)))
                continue
            if re.fullmatch(r"[\d.,\s]+", token):
                found = _DATE_FIELD_RE.findall(token)
                if found:
                    line_dates.extend(found)
                    continue
            line_text.append(token)

        if line_weekday is not None and cur_weekday is not None:
            flush()
        cur_text.extend(line_text)
        if line_weekday is not None:
            cur_weekday = line_weekday
        cur_dates.extend(line_dates)

    flush()
    return blocks


def parse_holiday_shifts(prose_lines: list[str]) -> dict[date, date]:
    """Holiday shifts from "01.01.2026 (svoz se posouvá na pátek 02.01.2026)"."""
    shifts = {}
    for match in _HOLIDAY_SHIFT_RE.finditer(" ".join(prose_lines)):
        source_day = _parse_date(match.group(1))
        target_day = _parse_date(match.group(2))
        if source_day and target_day:
            shifts[source_day] = target_day
    if not shifts:
        _LOGGER.warning(
            "smolo_cz: could not read the holiday-shift sentence from the PDF; "
            "holiday shifts are not applied."
        )
    return shifts


def parse_sparse_bio_weeks(prose_lines: list[str]) -> set[int] | None:
    """The ISO weeks of the once-a-month organic rounds in Jan, Feb and Dec."""
    match = _BIO_WEEKS_RE.search(" ".join(prose_lines))
    if not match:
        _LOGGER.warning(
            "smolo_cz: could not read the 'BIO 1x/month in Jan/Feb/Dec' week "
            "numbers from the PDF; assuming every even week in those months."
        )
        return None
    weeks = {
        int(chunk.strip().rstrip("."))
        for chunk in match.group(1).split(",")
        if chunk.strip().rstrip(".").isdigit()
    }
    return weeks or None


def parse_schedule(page1: str, page2: str) -> SmoloSchedule:
    """Read both pages' layout text into a :class:`SmoloSchedule`."""
    rows, prose = parse_district_table(page1)
    year = parse_year(page1)
    if not rows or year is None:
        raise ValueError("Could not read the SKO/BIO schedule table from the PDF.")
    return SmoloSchedule(
        year=year,
        rows=rows,
        holiday_shifts=parse_holiday_shifts(prose),
        sparse_bio_weeks=parse_sparse_bio_weeks(prose),
        blocks=parse_sorted_table(page2),
        sorted_year=parse_year(page2) or year,
    )


class SmoloScheduleParser:
    """Read the SMOLO Třinec schedule PDF (two pages, layout-mode text)."""

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> SmoloSchedule:
        from io import BytesIO

        from pypdf import PdfReader

        pages = PdfReader(BytesIO(response.content)).pages
        texts = [(page.extract_text(extraction_mode="layout") or "") for page in pages]
        first = texts[0] if texts else ""
        response_shape.expect(
            "ČÁST MĚSTA" in first,
            source_name=response_shape.source_name(source),
            detail="PDF has no 'ČÁST MĚSTA' table on page 1 (changed layout or image-only?)",
            raw=first[:500],
        )
        return parse_schedule(first, texts[1] if len(texts) > 1 else "")


def match_rows(
    rows: list[DistrictRow], district: str, street: str = ""
) -> list[DistrictRow]:
    """The page-1 rows for a district, narrowed by street when it is split."""
    target = normalize(district)
    matches = [
        row for row in rows if any(normalize(n) == target for n in row.district_names)
    ]
    if not matches:
        names = sorted({n for row in rows for n in row.district_names})
        raise SourceArgumentNotFoundWithSuggestions("district", district, names)
    if len(matches) == 1:
        return matches

    target_street = normalize(street) if street else ""
    if target_street:
        by_street = [r for r in matches if target_street in normalize(r.street_text)]
        if by_street:
            return by_street

    raise SourceArgumentNotFoundWithSuggestions(
        "street" if target_street else "district",
        street if target_street else district,
        [f"{row.district_raw} ({row.street_text})" for row in matches],
    )


def match_blocks(blocks: list[SortedBlock], district: str) -> list[SortedBlock]:
    """The page-2 blocks naming a district."""
    target = normalize(district)
    matches = [b for b in blocks if target in normalize(b.joined_text)]
    # The Nebory yellow (plastic) and blue (paper) rows name Nebory only once,
    # centred between the two rows; attach both explicitly.
    if target == "nebory":
        for block in blocks:
            text = normalize(block.joined_text)
            if (
                ("nadoba" in text or "pytle" in text)
                and block not in matches
                and ("zluta" in text or "modra" in text)
            ):
                matches.append(block)
    return matches


def sorted_label(block: SortedBlock) -> str:
    """The label of a page-2 block: yellow, blue or plain sorted waste."""
    text = normalize(block.joined_text)
    if "zluta" in text:
        return SORTED_YELLOW
    if "modra" in text:
        return SORTED_BLUE
    return SORTED


def _year_days(year: int) -> Iterator[date]:
    day = date(year, 1, 1)
    while day.year == year:
        yield day
        day += timedelta(days=1)


def expand_rows(
    schedule: SmoloSchedule, district: str, street: str = ""
) -> list[tuple[date, str]]:
    """``(date, label)`` rows for a district over the PDF's year."""
    result: list[tuple[date, str]] = []
    shifts = schedule.holiday_shifts

    for row in match_rows(schedule.rows, district, street):
        bio_weekday = 0 if row.bio_on_monday else row.weekday
        for day in _year_days(schedule.year):
            week = day.isocalendar()[1]
            odd_week = week % 2 == 1
            if day.weekday() == row.weekday and odd_week:
                result.append((shifts.get(day, day), RESIDUAL))
            if day.weekday() == bio_weekday and not odd_week:
                if (
                    day.month in (1, 2, 12)
                    and schedule.sparse_bio_weeks is not None
                    and week not in schedule.sparse_bio_weeks
                ):
                    continue
                result.append((shifts.get(day, day), ORGANIC))

    for block in match_blocks(schedule.blocks, district):
        label = sorted_label(block)
        for raw in block.dates:
            parts = [p for p in re.split(r"[.,]", raw) if p]
            try:
                result.append(
                    (date(schedule.sorted_year, int(parts[1]), int(parts[0])), label)
                )
            except (ValueError, IndexError):
                _LOGGER.warning("smolo_cz: skipping unreadable date %r", raw)
    return result


class SmoloScheduleExpander:
    """Turn the parsed PDF into ``(date, label)`` rows for the configured area."""

    def __call__(
        self, schedule: SmoloSchedule, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        params = source.params if source is not None else {}
        return expand_rows(
            schedule, params.get("district") or "", params.get("street") or ""
        )
