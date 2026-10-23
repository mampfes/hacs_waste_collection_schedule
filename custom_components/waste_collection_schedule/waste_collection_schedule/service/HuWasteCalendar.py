"""Pipeline component for the Hungarian "hulladéknaptár" PDF calendars.

Depónia Nonprofit Kft. (deponia.hu) and Siókom Nonprofit Kft. (siokom.hu) are
sister companies that publish the same annual calendar, exported from a
PowerPoint template: one table with a column per month and a row per separately
collected waste type (``szelektív``, ``zöldhulladék``, ...) listing the days of
the month ("3.,17.,31." or "1,8,15,22, 29"), and a sentence below it that
names the weekday(s) of the weekly general-waste round ("Vegyes
hulladékgyűjtési nap: KEDD,PÉNTEK"), optionally restricted to date ranges
("01.01-03.31 és 11.01-12.31 között CSÜTÖRTÖK") or moved by a public holiday
("2026.05.01. áthelyezésre kerül 2026.05.02").

:class:`CalendarParser` decodes the PDF into ``(date, label)`` records. The
labels are the Hungarian words printed in the PDF (plus :data:`GENERAL` and
:data:`BULKY` for the two rounds that are not table rows), which the source's
``ICSTransformer`` maps onto waste types. The month of a day cell is the month
header nearest to it in the layout text. A PDF without a year, without the
month header or without any date fails loudly instead of returning nothing.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, timedelta
from io import BytesIO
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import response_shape
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

#: Labels for the two rounds that are not rows of the month table.
GENERAL = "vegyes"
BULKY = "lomtalanítás"

MONTHS = {
    "január": 1,
    "február": 2,
    "március": 3,
    "április": 4,
    "május": 5,
    "június": 6,
    "július": 7,
    "augusztus": 8,
    "szeptember": 9,
    "október": 10,
    "november": 11,
    "december": 12,
}

WEEKDAYS = {
    "hétfő": 0,
    "kedd": 1,
    "szerda": 2,
    "csütörtök": 3,
    "péntek": 4,
    "szombat": 5,
    "vasárnap": 6,
}

_YEAR_RE = re.compile(r"(20\d{2})\.\s*évi\s+hulladéknaptár", re.IGNORECASE)
#: Day-list notations of a month cell: "14,28" / "1,8,15,22, 29" (Siókom).
PLAIN_CELLS = r"-|\d{1,2}(?:[.,]\s*\d{1,2}){1,6}\.?|\d{1,2}\.?"
#: and "3.,17.,31." / "14. 28" (Depónia).
DOTTED_CELLS = (
    r"-|\d{1,2}(?:\.,\d{1,2}){1,3}\.?|\d{1,2}[.,]\s{1,2}\d{1,2}"
    r"|\d{1,2}\.\d{1,2}\.?|\d{1,2}\.?"
)
_DAY_RE = re.compile(r"\d{1,2}")

_RANGE_NC = r"\d{1,2}\.\d{1,2}\s*-\s*\d{1,2}\.\d{1,2}"
_WD_NC = "|".join(WEEKDAYS)
_RANGED_RULE_RE = re.compile(
    rf"((?:{_RANGE_NC}(?:\s+és\s+{_RANGE_NC})*)\s+között)\s+"
    rf"(({_WD_NC})(?:\s+és\s+(?:{_WD_NC}))*)",
    re.IGNORECASE,
)
_RANGE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\s*-\s*(\d{1,2})\.(\d{1,2})")
_COMMUNAL_RE = re.compile(
    r"Vegyes\s+hulladékgyűjtési\s+nap\s*:(.*)", re.IGNORECASE | re.DOTALL
)
_COMMUNAL_END_RE = re.compile(
    r"Szolgáltató|Lomtalanítás|Kérjük|Hulladékudvar|20\d{2}", re.IGNORECASE
)
_ISO_POSTPONE_RE = re.compile(
    r"(20\d{2})\.(\d{2})\.(\d{2})\.[^.]*?áthelyezésre kerül\s*"
    r"(20\d{2})\.(\d{2})\.(\d{2})",
    re.IGNORECASE,
)
_HU_POSTPONE_RE = re.compile(
    r"áthelyezés:\s*(\w+)\s+(\d{1,2})\.\s*gyűjtés\s*(\w+)\s+(\d{1,2})",
    re.IGNORECASE,
)
_BULKY_ISO_RE = re.compile(
    r"Lomtalanítás\s*:?\s*(20\d{2})\.(\d{1,2})\.(\d{1,2})", re.IGNORECASE
)
_BULKY_HU_RE = re.compile(
    r"(20\d{2})\.\s*(" + "|".join(MONTHS) + r")\s+(\d{1,2})", re.IGNORECASE
)


def fold(value: str) -> str:
    """Case- and accent-insensitive form of ``value`` for comparing names."""
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    collapsed = re.sub(r"\s+", " ", stripped).strip().casefold()
    return re.sub(r"\s*-\s*", "-", collapsed)


def month_columns(line: str) -> list[tuple[int, int]] | None:
    """``(position, month)`` of the twelve month names in a header line."""
    low = line.lower()
    if "január" not in low or "december" not in low:
        return None
    cols = sorted(
        (low.find(name), number) for name, number in MONTHS.items() if name in low
    )
    return cols if len(cols) == 12 else None


def table_row_dates(
    line: str,
    year: int,
    columns: list[tuple[int, int]],
    types: Mapping[str, str],
    *,
    skip: re.Pattern[str],
    cells: re.Pattern[str] = re.compile(PLAIN_CELLS),
    max_length: int | None = None,
) -> list[tuple[date, str]]:
    """The dated cells of one table row, labelled with the row's waste type.

    ``types`` maps the (lowercase) row label printed in the PDF to the label to
    emit. Lines of running text that merely mention a type are ignored: they
    match ``skip``, exceed ``max_length`` or carry no day after the label.
    """
    if skip.search(line) or (max_length is not None and len(line) > max_length):
        return []
    pattern = r"\b(" + "|".join(re.escape(label) for label in types) + r")\b"
    match = re.search(pattern, line, re.IGNORECASE)
    if not match:
        return []
    after = line[match.end() :]
    if not re.search(r"\d|-", after):
        return []
    label = types[match.group(1).lower()]
    entries: list[tuple[date, str]] = []
    for cell in cells.finditer(after):
        token = cell.group()
        if token in ("-", "–", "—") or not _DAY_RE.search(token):
            continue
        position = match.end() + cell.start()
        month = min(columns, key=lambda col: abs(col[0] - position))[1]
        for day in (int(item) for item in _DAY_RE.findall(token)):
            try:
                entries.append((date(year, month, day), label))
            except ValueError:
                _LOGGER.debug("Ignoring invalid date %s-%s-%s", year, month, day)
    return entries


def weekdays_in(text: str) -> list[int]:
    """The weekdays (Monday is 0) named in ``text``, in any case or accent."""
    folded = fold(text)
    return sorted(
        {wd for name, wd in WEEKDAYS.items() if re.search(rf"\b{fold(name)}\b", folded)}
    )


def dates_in_range(start: date, end: date, weekdays: Iterable[int]) -> list[date]:
    """Every date from ``start`` to ``end`` (inclusive) on one of ``weekdays``."""
    wanted = set(weekdays)
    return [
        start + timedelta(days=offset)
        for offset in range((end - start).days + 1)
        if (start + timedelta(days=offset)).weekday() in wanted
    ]


def general_waste_dates(text: str, year: int) -> list[date]:
    """The weekly general-waste days from the "Vegyes hulladékgyűjtési nap" text.

    Either plain weekdays for the whole year ("KEDD,PÉNTEK") or one rule per
    date range ("01.01-03.31 és 11.01-12.31 között CSÜTÖRTÖK").
    """
    match = _COMMUNAL_RE.search(text)
    if not match:
        return []
    rest = _COMMUNAL_END_RE.split(match.group(1), maxsplit=1)[0]
    if _RANGE_RE.search(match.group(1)):
        # the range rules contain no year, so cut only at the footer words
        rest = re.split(
            r"Szolgáltató|Lomtalanítás|Kérjük|Hulladékudvar",
            match.group(1),
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
    rest = re.sub(r"\s+", " ", rest).strip()
    dated: set[date] = set()
    if _RANGE_RE.search(rest):
        for rule in _RANGED_RULE_RE.finditer(rest):
            weekdays = weekdays_in(rule.group(2))
            for start_m, start_d, end_m, end_d in _RANGE_RE.findall(rule.group(1)):
                try:
                    start = date(year, int(start_m), int(start_d))
                    end = date(year, int(end_m), int(end_d))
                except ValueError:
                    continue
                dated.update(dates_in_range(start, end, weekdays))
    else:
        weekdays = weekdays_in(rest)
        if weekdays:
            dated.update(dates_in_range(date(year, 1, 1), date(year, 12, 31), weekdays))
    return sorted(dated)


def postponements(text: str, year: int) -> list[tuple[date, date]]:
    """``(from, to)`` pairs of the holiday moves announced in the PDF."""
    moves: list[tuple[date, date]] = []
    for match in _ISO_POSTPONE_RE.finditer(text):
        try:
            moves.append(
                (
                    date(int(match.group(1)), int(match.group(2)), int(match.group(3))),
                    date(int(match.group(4)), int(match.group(5)), int(match.group(6))),
                )
            )
        except ValueError:
            continue
    for match in _HU_POSTPONE_RE.finditer(text):
        src_month = MONTHS.get(match.group(1).lower())
        dst_month = MONTHS.get(match.group(3).lower())
        if not src_month or not dst_month:
            continue
        try:
            moves.append(
                (
                    date(year, src_month, int(match.group(2))),
                    date(year, dst_month, int(match.group(4))),
                )
            )
        except ValueError:
            continue
    return moves


def apply_postponements(
    dates: Iterable[date], moves: Iterable[tuple[date, date]]
) -> list[date]:
    """``dates`` with every date named as the start of a move shifted."""
    remaining = set(dates)
    for src, dst in moves:
        if src in remaining:
            remaining.remove(src)
            remaining.add(dst)
    return sorted(remaining)


def bulky_dates(text: str) -> list[date]:
    """Dated bulky-waste collections ("Lomtalanítás: 2026.05.16.")."""
    dates: set[date] = set()
    for match in _BULKY_ISO_RE.finditer(text):
        try:
            dates.add(
                date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            )
        except ValueError:
            continue
    if re.search(r"Lomtalanítási\s+időpontok", text, re.IGNORECASE):
        for match in _BULKY_HU_RE.finditer(text):
            try:
                dates.add(
                    date(
                        int(match.group(1)),
                        MONTHS[match.group(2).lower()],
                        int(match.group(3)),
                    )
                )
            except ValueError:
                continue
    return sorted(dates)


class CalendarParser(Parser["list[tuple[date, str]]"]):
    """Decode a Depónia / Siókom hulladéknaptár PDF into ``(date, label)``.

    Args:
        types: the table row labels to read (lowercase, as printed) and the
            label emitted for each.
        skip: a pattern marking running-text lines that mention a type.
        cells: the day-list notation of a month cell, :data:`PLAIN_CELLS` or
            :data:`DOTTED_CELLS`.
        max_row_length: ignore lines longer than this (running text).
        bulky: also read dated bulky-waste collections, emitted as
            :data:`BULKY`.
        holiday_moves: apply the announced holiday moves of the weekly
            general-waste round.
    """

    def __init__(
        self,
        *,
        types: Mapping[str, str],
        skip: str = r"gyűjtés:|gyűjtésbe|gyűjtést|anyagok",
        cells: str = PLAIN_CELLS,
        max_row_length: int | None = None,
        bulky: bool = False,
        holiday_moves: bool = False,
    ):
        self.types = {key.lower(): value for key, value in types.items()}
        self.skip = re.compile(skip, re.IGNORECASE)
        self.cells = re.compile(cells)
        self.max_row_length = max_row_length
        self.bulky = bulky
        self.holiday_moves = holiday_moves

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        from pypdf import PdfReader

        name = response_shape.source_name(source)
        reader = PdfReader(BytesIO(response.content))
        layouts = [
            page.extract_text(extraction_mode="layout") or "" for page in reader.pages
        ]
        plains = [page.extract_text() or "" for page in reader.pages]
        combined = "\n".join([*layouts, *plains])

        year_match = _YEAR_RE.search(combined)
        response_shape.expect(
            year_match is not None,
            source_name=name,
            detail="no 'YYYY. évi hulladéknaptár' heading in the PDF",
            raw=combined[:500],
        )
        year = int(year_match.group(1))  # type: ignore[union-attr]

        columns = None
        table_page = 0
        for index, layout in enumerate(layouts):
            for line in layout.splitlines():
                columns = month_columns(line)
                if columns:
                    break
            if columns:
                table_page = index
                break
        response_shape.expect(
            columns is not None,
            source_name=name,
            detail="no month table in the PDF",
            raw=combined[:500],
        )

        dated: list[tuple[date, str]] = []
        for line in layouts[table_page].splitlines():
            dated.extend(
                table_row_dates(
                    line,
                    year,
                    columns,  # type: ignore[arg-type]
                    self.types,
                    skip=self.skip,
                    cells=self.cells,
                    max_length=self.max_row_length,
                )
            )

        weekly = general_waste_dates(plains[table_page], year) or general_waste_dates(
            layouts[table_page], year
        )
        if weekly and self.holiday_moves:
            weekly = apply_postponements(weekly, postponements(combined, year))
        dated.extend((when, GENERAL) for when in weekly)
        if self.bulky:
            dated.extend((when, BULKY) for when in bulky_dates(combined))

        response_shape.expect(
            bool(dated),
            source_name=name,
            detail="no collection dates found in the PDF",
            raw=combined[:500],
        )
        return sorted(dated)
