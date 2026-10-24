"""Pipeline components for waste calendars published as a text PDF day grid.

The text-layer counterpart to :mod:`waste_collection_schedule.service.PdfImageCalendar`.
Where that module reads a calendar whose page is one raster image, this one reads
the common printed layout that still carries a text layer: a grid of one row per
day, each row starting with the day number and a weekday abbreviation and then
naming that day's collections in free text::

    2FR H.müll / D.men.  Bio
    3SA
    6DI Glas / verre   Papier

Such calendars usually print no month headers at all: the month is implied by the
column the row sits in, which ``pypdf`` flattens away. What survives is that the
day numbers run 1..31 and then restart, so a day number lower than the previous
one means the next month has begun. That, plus the page a row came from, is
enough to date every row, and it is the same trick for every provider printing
this layout, which is why it lives here rather than in a source.

Two things stay per-provider and are passed in as data:

* :class:`LabelRule` -- the vocabulary. Which text in a cell means which waste
  label (a commune may write "H.müll" and "D.men." for the same round).
* :class:`ExtraDatesRule` -- optional. A round whose dates the grid does not
  show reliably (a coloured overlay can hide a cell), listed instead as plain
  dates in the calendar's info text.

Two optional refinements cover printed variants of the same layout:

* ``codes`` -- a calendar that prints short codes glued together in the cell
  ("BB1GB", "PSMPS") rather than words. Each code maps to a label and a cell
  token made only of codes is split into them.
* ``weekday_order`` -- the weekday abbreviations Monday first. With it, each
  run of day numbers is dated by the weekdays it prints rather than by its
  position, which both reads a page whose month blocks are not in calendar
  order (pypdf emits some multi-column pages column by column, in an order of
  its own) and fails loudly when the grid does not fit the calendar year at all.

The label each row maps to is a plain string; the source's transformer
(typically ``ICSTransformer``) maps those labels to canonical ``WasteType``
values, so icons and multilingual names come from the shared vocabulary rather
than being declared here.
"""

from __future__ import annotations

import calendar
import re
from datetime import date
from typing import TYPE_CHECKING, Any, NamedTuple

from waste_collection_schedule import recurrence, response_shape
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from waste_collection_schedule.base_source import BaseSource

# "2FR H.müll / D.men.  Bio" -> day, weekday abbreviation, free-text content.
DEFAULT_LINE_PATTERN = r"^(\d{1,2})([A-Za-z]{2,3})\s*(.*)"

# A full date in an info-text section, e.g. "17.02.2026".
DEFAULT_DATE_PATTERN = r"(\d{2})\.(\d{2})\.(\d{4})"

# Weekday abbreviations Monday first, upper-cased, for ``weekday_order``:
# ("MO", "DI", ..., "SO") and ("LUN", "MAR", ..., "DIM").
GERMAN_WEEKDAY_ORDER = tuple(
    name.upper() for name in recurrence.weekday_names("de", abbreviated=True)
)
FRENCH_WEEKDAY_ORDER = tuple(
    name.upper() for name in recurrence.weekday_names("fr", abbreviated=True)
)

# The German set, the usual one for a DE/LU/AT printed calendar.
GERMAN_WEEKDAYS = frozenset(GERMAN_WEEKDAY_ORDER)

# A cell token that looks like a code (upper-case letters, digits after the
# first) but is not made of known codes is preserved verbatim, so a code the
# provider introduces surfaces as an unresolved label instead of vanishing.
_CODE_LIKE = re.compile(r"^[A-Z][A-Z0-9]{0,5}$")


class LabelRule(NamedTuple):
    """A waste label and the regex that spots it in one grid cell's free text.

    ``pattern`` is searched (not matched) against the cell text, case
    sensitively, so ``"Glas|verre"`` covers a bilingual calendar and
    ``r"\\bBio\\b"`` avoids matching "Biotonne-Info". Rules are evaluated in
    declaration order and every match contributes a record, because one cell
    routinely names several rounds.
    """

    label: str
    pattern: str


class ExtraDatesRule(NamedTuple):
    """Dates for one label listed in the calendar's info text, not the grid.

    ``section`` is a regex searched (with ``DOTALL``) against the whole
    document text; its first capture group is the block of text holding the
    dates, which is then scanned for the parser's ``date_pattern``. Dates the
    grid already produced for this label are not added twice.
    """

    label: str
    section: str


class DayGridCalendarParser(Parser["list[tuple[date, str]]"]):
    """Read a text PDF laid out as a day-per-line calendar grid.

    Consumes the PDF response (typically from
    :class:`~waste_collection_schedule.retrievers.PdfLinkRetriever`, whose
    response carries the chosen document's URL) and emits ``(date, label)``
    records for an ``ICSTransformer``.

    The calendar year is read off the document URL, because these calendars are
    republished under a new URL every year and carry no machine-readable year
    inside. A URL that does not match ``year_pattern`` falls back to the current
    year.

    Args:
        labels: the provider's vocabulary, in evaluation order.
        months_per_page: how many months one page covers. Page ``p`` therefore
            starts at month ``1 + p * months_per_page``: 6 for the usual
            two-page Jan-Jun / Jul-Dec calendar, 12 for a single-page year, 1
            for a page per month. Rows that would fall past December are
            dropped rather than rolled into the next year.
        year_pattern: regex searched against the document URL; capture group 1
            is the four-digit year.
        line_pattern: regex matched against each stripped line; groups are
            (day number, weekday abbreviation, cell text).
        weekdays: accepted weekday abbreviations, compared upper-cased. This is
            what separates real grid rows from any other line that happens to
            start with digits. ``None`` accepts whatever ``line_pattern``
            matched.
        extra_dates: optional info-text rounds, see :class:`ExtraDatesRule`.
        date_pattern: regex for a full date inside an ``extra_dates`` section;
            groups are (day, month, year).
        codes: optional ``{code: label}`` for a calendar printing short codes
            glued together ("BB1GB" is B, B1 and GB). Every whitespace-separated
            token of a cell that consists only of codes is split into them (the
            split backtracks, so "PSMPS" reads as P, SM, PS) and each yields its
            label. A code-like token that does not split is yielded verbatim.
            Combines with ``labels``; either may be empty but not both.
        layout: build each grid row from the positioned words of the page
            (pdfminer) instead of pypdf's text: for a calendar whose round
            labels are drawn apart from their day row, so plain text lists them
            after the days. A word joins the day row whose day number sits
            nearest it vertically.
        year_text_pattern: optional regex searched in the document text
            before ``year_pattern`` is tried on the URL, for a calendar
            published under a URL without a year.
        weekday_order: optional weekday abbreviations, Monday first. When set,
            it replaces ``weekdays`` as the row filter and each run of day
            numbers (a month block) is dated by matching its printed weekdays
            against the months its page covers, so blocks emitted out of order
            land in the right month. With ``months_per_page=None`` the blocks
            are read in calendar order wherever the pages put them (a calendar
            with a cover or info pages, or one running into the next year);
            runs shorter than a month are then ignored. A block that fits no month raises
            ``ResponseShapeError``: the year read off the URL is wrong or the
            layout changed.
    """

    def __init__(
        self,
        *,
        labels: Sequence[LabelRule],
        months_per_page: int | None = 6,
        year_pattern: str = r"(20\d\d)",
        line_pattern: str = DEFAULT_LINE_PATTERN,
        weekdays: Iterable[str] | None = None,
        extra_dates: Sequence[ExtraDatesRule] = (),
        date_pattern: str = DEFAULT_DATE_PATTERN,
        codes: Mapping[str, str] | None = None,
        weekday_order: Sequence[str] | None = None,
        layout: bool = False,
        year_text_pattern: str | None = None,
    ):
        if not labels and not codes:
            raise ValueError("DayGridCalendarParser needs labels or codes")
        self._labels = [(rule.label, re.compile(rule.pattern)) for rule in labels]
        self._months_per_page = months_per_page
        if months_per_page is None and weekday_order is None:
            raise ValueError("months_per_page=None needs weekday_order")
        self._layout = layout
        self._year_text = re.compile(year_text_pattern) if year_text_pattern else None
        self._year = re.compile(year_pattern)
        self._line = re.compile(line_pattern)
        self._codes = dict(codes or {})
        # Longest first, so "B1" is tried before "B" at each position.
        self._code_list = sorted(self._codes, key=len, reverse=True)
        self._weekday_order = (
            None if weekday_order is None else [w.upper() for w in weekday_order]
        )
        if self._weekday_order is not None and len(self._weekday_order) != 7:
            raise ValueError("weekday_order needs seven abbreviations, Monday first")
        if self._weekday_order is not None:
            weekdays = self._weekday_order
        self._weekdays = (
            None if weekdays is None else frozenset(w.upper() for w in weekdays)
        )
        self._extra_dates = [
            (rule.label, re.compile(rule.section, re.DOTALL)) for rule in extra_dates
        ]
        self._date = re.compile(date_pattern)

    def _year_of(self, url: str) -> int:
        match = self._year.search(url)
        return int(match.group(1)) if match else date.today().year

    def _split_codes(self, token: str) -> list[str] | None:
        """Split a glued token into known codes, or None if it does not split."""
        if not token:
            return []
        for code in self._code_list:
            if token.startswith(code):
                rest = self._split_codes(token[len(code) :])
                if rest is not None:
                    return [code, *rest]
        return None

    def _labels_in(self, content: str) -> list[str]:
        found = [label for label, pattern in self._labels if pattern.search(content)]
        if self._codes:
            for token in content.split():
                parts = self._split_codes(token)
                if parts:
                    found.extend(self._codes[code] for code in parts)
                elif parts is None and _CODE_LIKE.match(token):
                    found.append(token)
        return found

    def _runs(self, page_text: str) -> list[list[tuple[int, str, str]]]:
        """The page's grid rows, split into runs where the day number restarts."""
        runs: list[list[tuple[int, str, str]]] = []
        prev_day = 0
        for line in page_text.split("\n"):
            match = self._line.match(line.strip())
            if not match:
                continue
            weekday = match.group(2).upper()
            if self._weekdays is not None and weekday not in self._weekdays:
                continue
            day = int(match.group(1))
            if not runs or day < prev_day:
                # The day number restarted: the next month has begun.
                runs.append([])
            prev_day = day
            runs[-1].append((day, weekday, match.group(3).strip()))
        return runs

    @staticmethod
    def _fits(
        run: list[tuple[int, str, str]], year: int, month: int, order: list[str]
    ) -> bool:
        length = calendar.monthrange(year, month)[1]
        return all(
            day <= length and date(year, month, day).weekday() == order.index(weekday)
            for day, weekday, _ in run
        )

    def _month_of_run(
        self,
        run: list[tuple[int, str, str]],
        year: int,
        candidates: list[int],
        order: list[str],
        source: BaseSource | None,
    ) -> int:
        fitting = [m for m in candidates if self._fits(run, year, m, order)]
        # A complete block also pins the month length (February vs March).
        last_day = max(day for day, _, _ in run)
        exact = [m for m in fitting if calendar.monthrange(year, m)[1] == last_day]
        choices = exact or fitting
        response_shape.expect(
            bool(choices),
            source_name=response_shape.source_name(source),
            detail=(
                f"a calendar block starting {run[0][0]} {run[0][1]} matches no "
                f"month of {year}; wrong year or changed layout"
            ),
            raw=" | ".join(f"{d} {w} {c}" for d, w, c in run[:10]),
        )
        # Ambiguous only for a partial block; then calendar order decides.
        return choices[0]

    def _grid_records(
        self, page_texts: list[str], year: int, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        if self._months_per_page is None:
            return self._sequential_records(page_texts, year, source)
        records: list[tuple[date, str]] = []
        for page_num, page_text in enumerate(page_texts):
            first = 1 + page_num * self._months_per_page
            remaining = [
                m for m in range(first, first + self._months_per_page) if m <= 12
            ]
            for index, run in enumerate(self._runs(page_text)):
                if self._weekday_order is not None:
                    response_shape.expect(
                        bool(remaining),
                        source_name=response_shape.source_name(source),
                        detail=f"page {page_num + 1} has more month blocks than "
                        f"the {self._months_per_page} months it should cover",
                    )
                    month = self._month_of_run(
                        run, year, remaining, self._weekday_order, source
                    )
                    remaining.remove(month)
                else:
                    month = first + index
                records.extend(self._run_records(run, year, month))
        return records

    def _sequential_records(
        self, page_texts: list[str], year: int, source: BaseSource | None
    ) -> list[tuple[date, str]]:
        """Month blocks in calendar order, wherever the pages put them.

        The first block is dated by its weekdays within ``year``, every later
        one is the month after the previous, rolling into the next year, and
        must fit its weekdays too. Runs shorter than a month (dated lines of an
        info page) are skipped.
        """
        order = self._weekday_order or []
        records: list[tuple[date, str]] = []
        current: tuple[int, int] | None = None
        for page_text in page_texts:
            for run in self._runs(page_text):
                if len(run) < 28:
                    continue
                if current is None:
                    current = (
                        year,
                        self._month_of_run(
                            run, year, list(range(1, 13)), order, source
                        ),
                    )
                else:
                    y, m = current
                    current = (y + 1, 1) if m == 12 else (y, m + 1)
                    response_shape.expect(
                        self._fits(run, current[0], current[1], order),
                        source_name=response_shape.source_name(source),
                        detail=(
                            f"the month block after {y}-{m:02d} does not fit "
                            f"{current[0]}-{current[1]:02d}; changed layout"
                        ),
                        raw=" | ".join(f"{d} {w} {c}" for d, w, c in run[:10]),
                    )
                records.extend(self._run_records(run, *current))
        return records

    def _run_records(
        self, run: list[tuple[int, str, str]], year: int, month: int
    ) -> list[tuple[date, str]]:
        records: list[tuple[date, str]] = []
        for day, _, content in run:
            for label in self._labels_in(content):
                try:
                    records.append((date(year, month, day), label))
                except ValueError:
                    # Past December, or a day the month does not have.
                    pass
        return records

    def _extra_records(
        self, full_text: str, existing: list[tuple[date, str]]
    ) -> list[tuple[date, str]]:
        records: list[tuple[date, str]] = []
        for label, section in self._extra_dates:
            match = section.search(full_text)
            if not match:
                continue
            seen = {d for d, found in existing if found == label}
            for found in self._date.finditer(match.group(1)):
                try:
                    listed = date(
                        int(found.group(3)), int(found.group(2)), int(found.group(1))
                    )
                except ValueError:
                    continue
                if listed not in seen:
                    records.append((listed, label))
                    seen.add(listed)
        return records

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(response.content))
        plain_texts = [(page.extract_text() or "") for page in reader.pages]
        full_text = "\n".join(plain_texts)
        page_texts = (
            _layout_page_texts(response, source, self._weekdays)
            if self._layout
            else plain_texts
        )

        year = self._year_of(getattr(response, "url", "") or "")
        if self._year_text is not None and (match := self._year_text.search(full_text)):
            year = int(match.group(1))
        records = self._grid_records(page_texts, year, source)
        records.extend(self._extra_records(full_text, records))
        return records


def _layout_page_texts(
    response: Any, source: BaseSource | None, weekdays: frozenset[str] | None = None
) -> list[str]:
    """Each page's day rows rebuilt from positioned words, one line per day.

    A day row starts with a day number followed by a word on the same line (its
    weekday, one of ``weekdays`` when given); every other word of the page joins
    the day row nearest it vertically, within half the spacing of two rows, in
    reading order.
    """
    from waste_collection_schedule.parsers import PdfWordLayoutParser

    layout = PdfWordLayoutParser()(response, source)[0]
    pages = max((w.page for w in layout.words), default=-1) + 1
    texts: list[str] = []
    for page in range(pages):
        words = [w for w in layout.words if w.page == page]
        anchors = []
        for word in words:
            if not re.fullmatch(r"\d{1,2}", word.text):
                continue
            beside = [
                w
                for w in words
                if w is not word
                and abs(w.y - word.y) < 2.5
                and 0 < w.x - word.x < 60
                and w.text.isalpha()
                and (weekdays is None or w.text.upper() in weekdays)
            ]
            if beside:
                weekday = min(beside, key=lambda w: w.x - word.x)
                anchors.append((word, weekday))
        if len(anchors) < 2:
            texts.append("")
            continue
        anchors.sort(key=lambda pair: -pair[0].y)
        gaps = [anchors[i][0].y - anchors[i + 1][0].y for i in range(len(anchors) - 1)]
        reach = sorted(gaps)[len(gaps) // 2] / 2
        rows: dict[int, list[Any]] = {i: [] for i in range(len(anchors))}
        used = {id(w) for pair in anchors for w in pair}
        for word in words:
            if id(word) in used:
                continue
            index = min(
                range(len(anchors)), key=lambda i: abs(anchors[i][0].y - word.y)
            )
            if abs(anchors[index][0].y - word.y) <= reach:
                rows[index].append(word)
        lines = []
        for index, (day, weekday) in enumerate(anchors):
            rest = " ".join(w.text for w in sorted(rows[index], key=lambda w: w.x))
            lines.append(f"{day.text} {weekday.text} {rest}".rstrip())
        texts.append("\n".join(lines))
    return texts
