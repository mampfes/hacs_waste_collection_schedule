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

The label each row maps to is a plain string; the source's transformer
(typically ``ICSTransformer``) maps those labels to canonical ``WasteType``
values, so icons and multilingual names come from the shared vocabulary rather
than being declared here.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any, NamedTuple

from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from waste_collection_schedule.base_source import BaseSource

# "2FR H.müll / D.men.  Bio" -> day, weekday abbreviation, free-text content.
DEFAULT_LINE_PATTERN = r"^(\d{1,2})([A-Za-z]{2,3})\s*(.*)"

# A full date in an info-text section, e.g. "17.02.2026".
DEFAULT_DATE_PATTERN = r"(\d{2})\.(\d{2})\.(\d{4})"

# German weekday abbreviations, the usual set for a DE/LU/AT printed calendar.
GERMAN_WEEKDAYS = frozenset({"MO", "DI", "MI", "DO", "FR", "SA", "SO"})


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
    """

    def __init__(
        self,
        *,
        labels: Sequence[LabelRule],
        months_per_page: int = 6,
        year_pattern: str = r"(20\d\d)",
        line_pattern: str = DEFAULT_LINE_PATTERN,
        weekdays: Iterable[str] | None = None,
        extra_dates: Sequence[ExtraDatesRule] = (),
        date_pattern: str = DEFAULT_DATE_PATTERN,
    ):
        self._labels = [(rule.label, re.compile(rule.pattern)) for rule in labels]
        self._months_per_page = months_per_page
        self._year = re.compile(year_pattern)
        self._line = re.compile(line_pattern)
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

    def _labels_in(self, content: str) -> list[str]:
        return [label for label, pattern in self._labels if pattern.search(content)]

    def _grid_records(self, page_texts: list[str], year: int) -> list[tuple[date, str]]:
        records: list[tuple[date, str]] = []
        for page_num, page_text in enumerate(page_texts):
            month = 1 + page_num * self._months_per_page
            prev_day = 0
            for line in page_text.split("\n"):
                match = self._line.match(line.strip())
                if not match:
                    continue
                if (
                    self._weekdays is not None
                    and match.group(2).upper() not in self._weekdays
                ):
                    continue
                day = int(match.group(1))
                if day < prev_day:
                    # The day number restarted: the next month has begun.
                    month += 1
                prev_day = day
                for label in self._labels_in(match.group(3).strip()):
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
        page_texts = [(page.extract_text() or "") for page in reader.pages]

        records = self._grid_records(
            page_texts, self._year_of(getattr(response, "url", "") or "")
        )
        records.extend(self._extra_records("\n".join(page_texts), records))
        return records
