"""Preprocessors: normalise parsed output into an iterable of records.

A preprocessor sits between ``parse`` and the transformer/classify step. It
takes whatever the parser produced and yields the individual records that the
transformer expects. This replaces the inline dict/list normalisation that
used to live in BaseSource.fetch().

Most sources need no preprocessor: the default (DefaultPreprocessor, wired into
BaseSource) normalises parser output the way the historical fetch() did — a
single dict becomes ``[dict]``, a falsy/None value becomes ``[]``, and an
existing iterable passes through unchanged.

Recurring-schedule sources set one explicitly to expand a base date + cadence
into individual collection dates::

    preprocess = preprocessors.RecurrenceExpander(_describe)
"""

import bisect
import datetime
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Protocol, TypeVar

from bs4 import Tag

from waste_collection_schedule import lookups, recurrence

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import PdfRow

InT = TypeVar("InT", contravariant=True)
OutT = TypeVar("OutT", covariant=True)


class Preprocessor(Protocol[InT, OutT]):
    """Normalise parsed output (InT) into an iterable of records (OutT).

    Receives the ``source`` instance so a preprocessor can read
    ``source.params`` while shaping records.
    """

    def __call__(
        self, records: InT, source: "BaseSource | None" = None
    ) -> Iterable[OutT]: ...


class DefaultPreprocessor(Preprocessor[Any, Any]):
    """Reproduce the historical BaseSource.fetch() normalisation.

    - A falsy value (None, empty list, etc.) yields nothing.
    - A single mapping yields one record.
    - Any other iterable passes through unchanged.
    """

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[Any]:
        if not records:
            return
        if isinstance(records, Mapping):
            yield records
            return
        yield from records


class FlattenGroups(Preprocessor[Any, Any]):
    """Flatten a ``{group: [record, ...]}`` mapping into a flat record stream.

    For a provider that groups its collections server-side -- most often by
    date, occasionally by round -- so the payload is a mapping of lists rather
    than the flat record list a transformer consumes. The default preprocessor
    would treat the whole mapping as a single record; this fans it out, yielding
    each list's entries individually in the mapping's own order::

        parse = parsers.JsonParser("dates")     # {"2026-07-03": [{...}, {...}], ...}
        preprocess = preprocessors.FlattenGroups()

    The group key is dropped, so use this only where each record carries
    everything the transformer needs. A date-keyed feed nearly always repeats
    the date inside the record; if it does not, the key is the only place the
    date exists and a source-specific expansion is the right tool instead.
    """

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[Any]:
        if not records:
            return
        for group in records.values():
            yield from group


class RowFilter(Preprocessor[Any, Any]):
    """Drop records a source must not publish, via a per-record predicate.

    The reusable home for "this feed carries more than this address wants".
    ``keep`` is ``callable(record, source) -> bool``; records it rejects never
    reach the transformer. Records pass through otherwise unchanged, so this
    composes with any record shape::

        preprocess = Compose(
            RowFilter(_keep_chosen_round),
            RowRelabel(rename={"Recycling (odd ISO weeks)": "Recycling"}),
        )

    Args:
        keep: ``callable(record, source) -> bool``.
    """

    def __init__(self, keep: "Callable[[Any, BaseSource | None], bool]"):
        self._keep = keep

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[Any]:
        for record in records:
            if self._keep(record, source):
                yield record


class RowRelabel(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """Rewrite the key of ``(date, key)`` rows before the transformer maps it.

    Keeps label tidying out of the transformer's ``type_value_map``, which
    should stay a plain vocabulary of the provider's own wording rather than
    accumulating one entry per spelling variant.

    Args:
        rename: a ``{old: new}`` mapping applied first; a key not listed is left
            alone. Use it to fold a variant spelling of a round onto the name
            the ``type_value_map`` knows.
        vocabulary: when set, a key that is *not* in ``vocabulary`` is retried as
            its first whitespace-separated word, and rewritten to that word if
            the word is in the vocabulary. This is the common case of a provider
            appending extra words to the bin name in an ICS SUMMARY
            ("Restmüll Abfuhr" -> "Restmüll") while leaving a genuinely
            multi-word label ("Gelbe(r) Sack/Tonne") untouched. Pass the
            transformer's ``type_value_map`` directly; its keys are exactly the
            vocabulary::

                preprocess = RowRelabel(vocabulary=_TYPE_VALUE_MAP)
                transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)
    """

    def __init__(
        self,
        rename: "Mapping[str, str] | None" = None,
        vocabulary: "Iterable[str] | None" = None,
    ):
        self._rename = dict(rename or {})
        self._vocabulary = None if vocabulary is None else frozenset(vocabulary)

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        for collection_date, key in records:
            renamed = self._rename.get(key)
            if renamed is not None:
                key = renamed
            if self._vocabulary is not None and key not in self._vocabulary:
                first_word = key.split(" ")[0]
                if first_word in self._vocabulary:
                    key = first_word
            yield collection_date, key


class HtmlGroupedDates(Preprocessor[list[Tag], "tuple[datetime.date, str]"]):
    """Expand per-round HTML containers into ``(date, key)`` rows.

    For a page that groups its dates *under* the round rather than beside it:
    one container element per waste type, identified by a CSS class, with the
    dates listed in repeated child elements beneath it. There is nothing on the
    dated child saying which round it belongs to, so the usual
    row-per-collection HTML transform does not fit.
    :class:`~waste_collection_schedule.parsers.HtmlParser` selects the
    containers and this reads the round off the container's class, pairing it
    with every date found beneath::

        parse = parsers.HtmlParser(".rest, .bio, .papier")
        preprocess = preprocessors.HtmlGroupedDates(
            keys=TYPE_MAP,
            date_pattern=r"\\d{2}\\.\\d{2}\\.\\d{4}",
            parse_date=date_parsers.for_format("%d.%m.%Y"),
        )
        transform = ICSTransformer(type_value_map=TYPE_MAP)

    A container whose classes name no known round is skipped, as is a child
    element with no date in its text (a heading or a "no collections" note).

    Args:
        keys: the CSS class tokens that name a round. Pass the transformer's
            ``type_value_map`` directly; its keys are exactly that set.
        date_pattern: regex searched against each child's text. Its first
            capturing group is the date string, or the whole match when the
            pattern has no group.
        parse_date: callable turning that string into a ``datetime.date``.
        item_selector: CSS selector for the dated children within a container
            (default ``"li"``).
    """

    def __init__(
        self,
        *,
        keys: Iterable[str],
        date_pattern: str,
        parse_date: Callable[[str], datetime.date],
        item_selector: str = "li",
    ):
        self._keys = frozenset(keys)
        self._date_pattern = re.compile(date_pattern)
        self._parse_date = parse_date
        self._item_selector = item_selector

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        for container in records:
            classes = container.get("class") or []
            key = next((token for token in classes if token in self._keys), None)
            if key is None:
                continue
            for item in container.select(self._item_selector):
                match = self._date_pattern.search(item.get_text())
                if match:
                    yield self._parse_date(match.group(1 if match.groups() else 0)), key


class ArgumentLookup(Preprocessor[Any, Any]):
    """Resolve a config argument against a table read out of the response.

    The shape behind every "which day is my street collected?" provider that
    publishes a list instead of an address API: the page names the rounds and
    their members, the user names their member, and the source has to match the
    two and say what the valid values were when it cannot. The matching and the
    "did you mean" error are :mod:`lookups`' job, so all the source supplies is
    the table::

        parse = parsers.HtmlParser("div.cpTabPanel")
        preprocess = Compose(
            preprocessors.ArgumentLookup(_street_weekdays, argument="street"),
            RecurrenceExpander(_describe),
        )

    Yields exactly one record, the resolved value (a weekday, a zone id, a list
    of weekdays: whatever the table maps to), so the stage after it describes one
    household's schedule rather than the whole town's. An argument that does not
    match raises ``SourceArgumentNotFoundWithSuggestions`` listing the table's
    keys, which is what the config flow shows the user.

    Args:
        table: ``callable(records, source) -> Mapping[str, V]`` building the
            lookup table from the parsed output. Key it the way the provider
            spells it: matching is case- and whitespace-insensitive, and the keys
            are what an unmatched argument is offered as suggestions.
        argument: the config param looked up, and the one blamed on a miss.
    """

    def __init__(
        self,
        table: "Callable[[Any, BaseSource | None], Mapping[str, Any]]",
        *,
        argument: str,
    ):
        self._table = table
        self._argument = argument

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[Any]:
        value = source.params.get(self._argument) if source is not None else None
        yield lookups.resolve(
            self._table(records, source), value, argument=self._argument
        )


class Deduplicate(Preprocessor[Any, Any]):
    """Drop repeated records, keeping the first occurrence and the input order.

    For a provider that publishes the same collection more than once: a printed
    calendar whose pages overlap at the month boundary, a postponement landing on
    a day that already has a collection, or two feeds merged server-side. Put it
    last in a :class:`Compose` so it sees the finished rows::

        preprocess = Compose(RecurrenceExpander(_describe), Deduplicate())

    Records must be hashable, which the usual ``(date, key)`` row is.
    """

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[Any]:
        seen: set[Any] = set()
        for record in records:
            if record in seen:
                continue
            seen.add(record)
            yield record


class PdfDayCell(NamedTuple):
    """One day cell of a printed calendar grid: its day number and its text.

    ``text`` is every text run the grid bound to this day, top of the cell
    first, joined by single spaces.
    """

    day: int
    text: str


class PdfColumn(NamedTuple):
    """One calendar column of a positioned-PDF page: its heading and its days.

    ``column`` is the column's position on the page, counting from zero at the
    left. ``header`` is its heading runs in page order (the month name, the year,
    whatever else is printed above the grid); ``cells`` are its day cells top to
    bottom.
    """

    page: int
    column: int
    header: tuple[str, ...]
    cells: tuple[PdfDayCell, ...]


class PdfCalendarColumns(Preprocessor["list[PdfRow]", PdfColumn]):
    """Group a positioned-PDF calendar into per-column day cells.

    For the printed month-grid calendar many municipalities publish: one or more
    month blocks per page, each with a heading and a grid of numbered day cells
    holding waste-type badges and the odd "collection suspended" note.
    :class:`~waste_collection_schedule.parsers.PdfTableParser` reads the page
    into positioned rows; this bins those runs into the calendar's own shape, so
    a source is left describing only what the badges and notes *mean*::

        parse = parsers.PdfTableParser(min_words=200)
        preprocess = Compose(
            preprocessors.PdfCalendarColumns(
                column_bounds=(300.0,),
                day_bands={0: (30.0, 66.0), 1: (340.0, 375.0)},
                header_y=845.0,
            ),
            RecurrenceExpander(_describe),   # column -> Schedule per collection
            Deduplicate(),
        )

    The binding rule is the one printed calendars obey: a day number anchors a
    cell, and every other run in the column belongs to the day whose number sits
    nearest it vertically. A column with no day numbers yields nothing, so a
    decorative or empty block costs the source no special casing.

    Args:
        column_bounds: the x positions splitting a page into columns, ascending.
            A page of two months side by side has one bound; a single-column
            calendar passes ``()``.
        day_bands: per column index, the ``(min, max)`` x range the day number
            occupies. The weekday abbreviation and the badges sit further right,
            so this is what separates the cell's anchor from its contents.
        header_y: runs above this y belong to the column heading, runs below to
            the grid. pdfminer's y grows upwards, so this is the baseline of the
            lowest heading line.
        day_range: the numbers accepted as a day anchor (default 1 to 31).
    """

    def __init__(
        self,
        *,
        column_bounds: Sequence[float],
        day_bands: Mapping[int, tuple[float, float]],
        header_y: float,
        day_range: tuple[int, int] = (1, 31),
    ):
        self._column_bounds = list(column_bounds)
        self._day_bands = dict(day_bands)
        self._header_y = header_y
        self._day_range = day_range

    def _column_of(self, x0: float) -> int:
        return bisect.bisect_right(self._column_bounds, x0)

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[PdfColumn]:
        rows = list(records)
        for page in sorted({row.page for row in rows}):
            page_rows = [row for row in rows if row.page == page]
            for index in sorted(self._day_bands):
                cells = self._cells(page_rows, index)
                if cells:
                    yield PdfColumn(
                        page=page,
                        column=index,
                        header=self._header(page_rows, index),
                        cells=cells,
                    )

    def _header(self, page_rows: "list[PdfRow]", index: int) -> tuple[str, ...]:
        return tuple(
            word.text
            for row in page_rows
            if row.y > self._header_y
            for word in row.words
            if self._column_of(word.x0) == index
        )

    def _cells(self, page_rows: "list[PdfRow]", index: int) -> tuple[PdfDayCell, ...]:
        low, high = self._day_bands[index]
        first_day, last_day = self._day_range
        anchors: list[tuple[float, int]] = []  # (y, day number)
        notes: list[tuple[float, str]] = []  # (y, text) of every other run
        for row in page_rows:
            if row.y >= self._header_y:
                continue
            for word in row.words:
                if self._column_of(word.x0) != index:
                    continue
                if (
                    low <= word.x0 <= high
                    and word.text.isdigit()
                    and first_day <= int(word.text) <= last_day
                ):
                    anchors.append((row.y, int(word.text)))
                else:
                    notes.append((row.y, word.text))

        if not anchors:
            return ()
        anchors.sort(key=lambda anchor: -anchor[0])

        bound: dict[int, list[tuple[float, str]]] = {i: [] for i in range(len(anchors))}
        for note_y, text in notes:
            nearest = min(
                range(len(anchors)), key=lambda i: abs(anchors[i][0] - note_y)
            )
            bound[nearest].append((note_y, text))

        return tuple(
            PdfDayCell(
                day=day,
                text=" ".join(
                    text for _, text in sorted(bound[i], key=lambda pair: -pair[0])
                ),
            )
            for i, (_, day) in enumerate(anchors)
        )


class TextGroupedDates(Preprocessor[str, "tuple[datetime.date, str]"]):
    """Expand a labelled plain-text schedule into ``(date, key)`` rows.

    The plain-text sibling of :class:`HtmlGroupedDates`, for a document with no
    markup to select on: a PDF text layer, or a text calendar, where a round's
    label introduces a run of dates and the next label ends it. A row whose
    dates wrap across several extracted lines is still captured as one segment,
    which is what makes this work on PDF text where the line breaks are an
    artefact of extraction rather than of the table::

        parse = parsers.PdfTextParser(min_chars=200)
        preprocess = preprocessors.TextGroupedDates(
            keys=TYPE_MAP,
            date_pattern=r"\\b(?P<month>\\d{2})\\.(?P<day>\\d{2})\\.",
            year_pattern=r"(\\d{4})\\.\\s*évi",
        )
        transform = ICSTransformer(type_value_map=TYPE_MAP)

    Text before the first label is ignored, as is a date that does not name a
    real day (a "31.11." typo, or a stray number pair that matched the pattern).

    Args:
        keys: the labels that introduce a round's dates, matched verbatim and
            case-sensitively, longest first so one label may contain another.
            Pass the transformer's ``type_value_map`` directly; its keys are
            exactly that set.
        date_pattern: regex scanned across each segment. It must carry named
            groups ``day`` and ``month``, and may carry ``year`` when the
            document dates each cell in full.
        year_pattern: for the usual per-year calendar whose cells omit the year
            and whose heading states it once: a regex searched against the whole
            document, its first group the four-digit year. Falls back to the
            current year when unset or unmatched, which is what a calendar
            published for the year in progress means.
    """

    def __init__(
        self,
        *,
        keys: Iterable[str],
        date_pattern: str,
        year_pattern: "str | None" = None,
    ):
        labels = sorted(keys, key=len, reverse=True)
        if not labels:
            raise ValueError("TextGroupedDates needs at least one key")
        self._label_re = re.compile(
            "(" + "|".join(re.escape(label) for label in labels) + ")"
        )
        self._date_re = re.compile(date_pattern)
        missing = {"day", "month"} - set(self._date_re.groupindex)
        if missing:
            raise ValueError(
                f"date_pattern is missing the named group(s) {sorted(missing)}"
            )
        self._year_re = re.compile(year_pattern) if year_pattern else None

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        text: str = records
        year = self._document_year(text)
        labels = list(self._label_re.finditer(text))
        for index, label in enumerate(labels):
            start = label.end()
            end = labels[index + 1].start() if index + 1 < len(labels) else len(text)
            for match in self._date_re.finditer(text[start:end]):
                collection_date = _date_from_groups(match.groupdict(), year)
                if collection_date is not None:
                    yield collection_date, label.group(1)

    def _document_year(self, text: str) -> int:
        if self._year_re is not None:
            match = self._year_re.search(text)
            if match:
                return int(match.group(1))
        return datetime.date.today().year


def _date_from_groups(
    groups: "Mapping[str, str | None]", year: int
) -> "datetime.date | None":
    """Build a date from ``day``/``month``/optional ``year`` groups, else None."""
    try:
        return datetime.date(
            int(groups.get("year") or year),
            int(groups["month"] or 0),
            int(groups["day"] or 0),
        )
    except ValueError:
        return None


@dataclass
class Schedule:
    """A recurring-collection descriptor: a start date, cadence and count.

    The reusable building block for sources that publish a *recurring* schedule
    (a base date plus a weekly/fortnightly cadence) rather than explicit dates.
    ``key`` is the waste-type string the transformer maps to a WasteType.
    """

    key: str
    start: datetime.date
    step: datetime.timedelta = field(default_factory=lambda: recurrence.WEEKLY)
    count: int = 1
    # When True, ``start`` is a (possibly historical) anchor: roll it forward by
    # ``step`` to the first occurrence on/after today before generating dates.
    anchor: bool = False
    # Optional season window. When ``until`` is set, the schedule runs in
    # windowed mode: ``start`` fixes only the cadence phase and every occurrence
    # within ``[not_before or start, until]`` is emitted (``count`` is ignored).
    # When ``until`` is unset, ``not_before`` simply drops earlier occurrences
    # from the count-based expansion. Model a seasonal schedule by yielding one
    # windowed Schedule per season segment (and none for no-collection months).
    not_before: datetime.date | None = None
    until: datetime.date | None = None
    # Optional ISO-week parity filter. When set to ``"even"`` / ``"odd"``, only
    # occurrences falling in an even- / odd-numbered ISO week are kept. This is
    # the correct way to express an "A week / B week" cadence keyed to the ISO
    # week number: pair it with ``step = WEEKLY`` and the parity selects every
    # other week, recomputed per date so it stays right across 53-week ISO years
    # (where naive fortnightly stepping would drift). The provider only has to
    # say which parity; no per-source week arithmetic.
    iso_week_parity: Literal["even", "odd"] | None = None
    # One-off adjustments the provider publishes alongside the cadence: ``extra``
    # dates are collected even though the cadence does not produce them (a
    # make-up run), ``exclude`` dates are not collected even though it does (a
    # public-holiday cancellation). ``extra`` dates are appended after the
    # projected ones and are not parity-filtered; ``exclude`` then drops matching
    # dates from both. Use these when the provider hands over explicit date
    # lists; use HolidayShift when a collection *moves* rather than disappears.
    extra: Sequence[datetime.date] = ()
    exclude: Sequence[datetime.date] = ()


class RecurrenceExpander(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """Expand recurring-schedule descriptors into ``(date, key)`` rows.

    The reusable home for date projection. A source supplies a ``describe``
    callable that turns each parsed record into zero or more :class:`Schedule`
    descriptors (the only provider-specific part — reading the base date and
    cadence out of the response). This expander then fans each descriptor out
    into concrete dates via the core :mod:`recurrence` helpers, and a plain
    transformer maps each ``key`` to a WasteType::

        def _describe(record, source):
            yield Schedule("general", base_date, recurrence.FORTNIGHTLY, 13)

        class Source(BaseSource):
            preprocess = RecurrenceExpander(_describe)
            transform = ICSTransformer(type_value_map={"general": GENERAL_WASTE})

    Args:
        describe: Callable ``(record, source) -> Iterable[Schedule]``.
    """

    def __init__(
        self,
        describe: Callable[[Any, "BaseSource | None"], Iterable[Schedule]],
    ):
        self._describe = describe

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        for record in records:
            for schedule in self._describe(record, source):
                if schedule.until is not None:
                    # Windowed: recurring_within already honours not_before.
                    dates: Iterable[datetime.date] = recurrence.recurring_within(
                        schedule.start,
                        schedule.step,
                        not_before=schedule.not_before or schedule.start,
                        until=schedule.until,
                    )
                else:
                    if schedule.anchor:
                        dates = recurrence.recurring_from_anchor(
                            schedule.start, schedule.step, schedule.count
                        )
                    else:
                        dates = recurrence.recurring(
                            schedule.start, schedule.step, schedule.count
                        )
                    # Count-based expansion ignores not_before; apply it here.
                    if schedule.not_before is not None:
                        dates = [d for d in dates if d >= schedule.not_before]
                if schedule.iso_week_parity is not None:
                    want_even = schedule.iso_week_parity == "even"
                    dates = [
                        d for d in dates if (d.isocalendar().week % 2 == 0) == want_even
                    ]
                if schedule.extra:
                    dates = [*dates, *schedule.extra]
                if schedule.exclude:
                    cancelled = set(schedule.exclude)
                    dates = [d for d in dates if d not in cancelled]
                for collection_date in dates:
                    yield collection_date, schedule.key


class Compose(Preprocessor[Any, Any]):
    """Apply several preprocessors in sequence; each consumes the previous output.

    Lets a source pipe a one-to-many stage into a follow-up adjustment stage::

        preprocess = Compose(
            RecurrenceExpander(_describe),   # records -> (date, key) rows
            HolidayShift(_adjust),           # shift/cancel rows on holidays
        )
    """

    def __init__(self, *stages: "Preprocessor"):
        self._stages = stages

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[Any]:
        for stage in self._stages:
            records = stage(records, source)
        return records


class HolidayShift(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """Adjust or cancel ``(date, key)`` rows via a per-collection lookup.

    For providers that move or cancel collections that land on a public holiday.
    ``adjust`` is a callable ``(date, key, source) -> datetime.date | None``: it
    returns the (possibly shifted) collection date, or ``None`` to cancel that
    collection. The holiday data itself is whatever the source fetched during
    ``retrieve`` and made available (typically stashed on ``source``)::

        preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_adjust))

        def _adjust(collection_date, key, source):
            return source.holidays.get(key, {}).get(collection_date, collection_date)
    """

    def __init__(
        self,
        adjust: "Callable[[datetime.date, str, BaseSource | None], datetime.date | None]",
    ):
        self._adjust = adjust

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        for collection_date, key in records:
            shifted = self._adjust(collection_date, key, source)
            if shifted is not None:
                yield shifted, key
