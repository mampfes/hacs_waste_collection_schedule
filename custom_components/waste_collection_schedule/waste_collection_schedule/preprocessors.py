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
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

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


class SplitLabels(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """Fan a row whose label names several rounds out into one row per round.

    For the provider that publishes a combined collection as one entry with the
    rounds joined in the text: "Rubbish Collection & Glass crate", "Papier /
    Bio". The transformer maps one label to one waste type, so the join has to
    be undone before it, and mapping every observed combination in the
    ``type_value_map`` does not scale (the combinations are the powerset of the
    rounds)::

        preprocess = preprocessors.SplitLabels(r"&")

    The ICS platform has its own version of this in
    :class:`~waste_collection_schedule.parsers.IcsParser`'s ``split_at``, which
    also title-cases each part. Reach for this one when the case must survive
    (the label is looked up somewhere case-sensitive), or when the rows come
    from anything other than an ICS feed.

    Empty parts are dropped, so a trailing or doubled separator costs nothing.

    Args:
        separator: regex the label is split on.
    """

    def __init__(self, separator: str):
        self._separator = re.compile(separator)

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        for collection_date, label in records:
            for part in self._separator.split(str(label)):
                stripped = part.strip()
                if stripped:
                    yield collection_date, stripped


class RoundAreaSelector(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """Keep the rows for this household's collection area, one area per round.

    For the municipal calendar that covers every collection area at once and
    tells them apart in the entry itself ("Restabfall 1", "Altpapier 5"), with
    the user supplying the area they are in for each round. Common in German
    districts, where the printed calendar assigns an Abfuhrbezirk per waste
    stream and one ICS feed serves the whole municipality. A surviving row is
    relabelled to its round alone, so the transformer's vocabulary stays the
    round names rather than every round/area combination::

        preprocess = preprocessors.RoundAreaSelector(
            rounds={"restabfall": "Restabfall", "altpapier": "Altpapier"},
            hint="check the PDF calendar for valid collection areas",
        )

    A round that never appears means the area number given for it is not one
    this calendar publishes, which is a wrong argument rather than an empty
    schedule, so it raises ``SourceArgumentNotFoundWithSuggestions`` naming that
    argument. The check runs over the whole feed, so this returns a list rather
    than streaming.

    Args:
        rounds: ``{config param name: round label}``. A row is kept when its
            round is one of these labels and its area equals
            ``str(params[name])``.
        pattern: regex matched against the entry, with named groups ``round``
            and ``area``. Defaults to a round name followed by a number.
        require: the param names whose round must appear, in the order they
            should be reported. Defaults to every key of ``rounds``.
        hint: the provider's own "where to find your area number" instruction,
            offered as the suggestion when a round is missing.
    """

    def __init__(
        self,
        *,
        rounds: Mapping[str, str],
        pattern: str = r"^(?P<round>.+?)\s+(?P<area>\d+)$",
        require: "Sequence[str] | None" = None,
        hint: str = "",
    ):
        self._rounds = dict(rounds)
        self._pattern = re.compile(pattern)
        self._require = tuple(rounds if require is None else require)
        self._hint = hint

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        params = source.params if source is not None else {}
        wanted = {label: str(params.get(name)) for name, label in self._rounds.items()}

        seen: set[str] = set()
        kept: list[tuple[datetime.date, str]] = []
        for collection_date, entry in records:
            match = self._pattern.match(str(entry).strip())
            if match is None:
                continue
            round_name = match.group("round")
            if wanted.get(round_name) != match.group("area"):
                continue
            seen.add(round_name)
            kept.append((collection_date, round_name))

        for name in self._require:
            if self._rounds[name] not in seen:
                raise SourceArgumentNotFoundWithSuggestions(
                    name, params.get(name), [self._hint] if self._hint else []
                )
        return kept


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


class RequireRecords(Preprocessor[Any, Any]):
    """Reject an empty record stream, blaming a config argument.

    The record-level twin of
    :class:`~waste_collection_schedule.parsers.ArgumentGuard`, for the provider
    that answers an unknown town or street with HTTP 200 and an empty result
    set. ``RAISE_ON_EMPTY`` already turns that into an argument error, but only
    at the end of the pipeline and without saying what the valid values were.
    This raises as soon as the lookup comes back empty, offering the provider's
    own list of them::

        preprocess = Compose(
            RequireRecords(argument="commune", suggestions=_list_communes),
            Disambiguate(argument="quartier", key=_quartier),
        )

    Args:
        argument: the config param blamed for the empty result.
        suggestions: optional ``callable(source) -> Iterable[str]`` returning the
            valid values, usually one cheap extra request to the provider's own
            index. It runs only on the failure path, so a healthy fetch pays
            nothing for it. If it fails in turn, the plainer ``hint`` error is
            raised instead, so a second outage cannot hide the first error.
        hint: guidance shown when no suggestions are available.
    """

    def __init__(
        self,
        *,
        argument: str,
        suggestions: "Callable[[BaseSource | None], Iterable[str]] | None" = None,
        hint: str = "",
    ):
        self._argument = argument
        self._suggestions = suggestions
        self._hint = hint

    def __call__(self, records: Any, source: "BaseSource | None" = None) -> list[Any]:
        candidates = list(records or [])
        if not candidates:
            self._reject(source)
        return candidates

    def _reject(self, source: "BaseSource | None") -> None:
        value = source.params.get(self._argument) if source is not None else None
        if self._suggestions is not None:
            try:
                options = list(self._suggestions(source))
            except Exception as e:
                raise SourceArgumentNotFound(self._argument, value, self._hint) from e
            raise SourceArgumentNotFoundWithSuggestions(self._argument, value, options)
        raise SourceArgumentNotFound(self._argument, value, self._hint)


class Disambiguate(Preprocessor[Any, Any]):
    """Narrow several candidate records to the one the user named.

    For the lookup that answers with every variant of the place asked for: one
    row per district of a town, one per round of a street. A single candidate
    needs no further input and passes straight through, which is what keeps the
    extra argument optional for the many places that have only one. Several mean
    the user has to say which, so an unset argument raises
    ``SourceArgumentRequiredWithSuggestions`` and an unrecognised one
    ``SourceArgumentNotFoundWithSuggestions``, both listing the candidates::

        preprocess = Compose(
            Disambiguate(
                argument="quartier",
                key=lambda row: row.get("quartier"),
                reason="{commune} has multiple districts; please specify one.",
            ),
            RecurrenceExpander(_describe),
        )

    Yields exactly one record, so the stage after it describes one household's
    schedule rather than the whole town's. Matching is case- and
    whitespace-insensitive (:mod:`lookups`).

    Args:
        argument: the config param naming the candidate, and the one blamed.
        key: ``callable(record) -> str`` reading a candidate's name off a
            record. Its value is what the argument is matched against and what
            the suggestions list.
        reason: why the argument is needed, shown when it was not given. May
            reference the source's other params by name, as above.
    """

    def __init__(
        self,
        *,
        argument: str,
        key: Callable[[Any], Any],
        reason: str = "the lookup matched several candidates; please name one.",
    ):
        self._argument = argument
        self._key = key
        self._reason = reason

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[Any]:
        candidates = list(records or [])
        if len(candidates) == 1:
            yield candidates[0]
            return
        if not candidates:
            return

        params = source.params if source is not None else {}
        value = params.get(self._argument)
        table = {self._name(record): record for record in candidates}
        if value is None:
            raise SourceArgumentRequiredWithSuggestions(
                self._argument, self._reason.format(**params), sorted(table)
            )
        yield lookups.resolve(table, value, argument=self._argument)

    def _name(self, record: Any) -> str:
        value = self._key(record)
        return "" if value is None else str(value).strip()


class SelectExactMatch(Preprocessor[Any, Any]):
    """Keep the rows of the one entity an over-broad lookup was asked for.

    The companion to :class:`Disambiguate` for the query that cannot be narrowed
    server-side: an address ``LIKE 'x%'`` clause, a street-name search, any
    lookup whose own argument is a fragment. It usually matches one property and
    returns that property's several rows (one per bin, one per charge), but a
    short fragment can match several distinct properties at once, and the
    provider does not order them meaningfully, so picking one silently would give
    the user a neighbour's schedule::

        preprocess = Compose(
            SelectExactMatch(argument="address", key=lambda row: row["Address_full"]),
            RecurrenceExpander(_describe),
            Deduplicate(),
        )

    One entity matched means the fragment was unambiguous and every row passes
    through, which is what keeps a partial address usable. Several mean the
    argument has to name one of them outright: an argument equal to a matched
    entity (case- and whitespace-insensitively, :mod:`lookups`) selects that
    entity's rows, and anything else raises ``SourceArgAmbiguousWithSuggestions``
    listing what matched, so the user can copy the full name back into the
    config.

    Unlike :class:`Disambiguate` this yields *every* row of the chosen entity,
    not one record, because the rows are the entity's collection rounds rather
    than competing candidates. It also blames the argument that ran the query
    rather than a second one, so there is no "please also specify" state.

    Args:
        argument: the config param that ran the lookup, and the one blamed.
        key: ``callable(record) -> str`` reading the entity's full name off a
            row. Rows with no name are dropped; an empty result yields nothing,
            so pair this with ``RAISE_ON_EMPTY`` on an address source.
        max_suggestions: how many matched names to offer. A one-word fragment can
            match hundreds, and a list that long helps nobody.
    """

    def __init__(
        self,
        *,
        argument: str,
        key: Callable[[Any], Any],
        max_suggestions: int = 10,
    ):
        self._argument = argument
        self._key = key
        self._max_suggestions = max_suggestions

    def __call__(self, records: Any, source: "BaseSource | None" = None) -> list[Any]:
        named = [(self._name(record), record) for record in records or []]
        named = [(name, record) for name, record in named if name]
        matched = sorted({name for name, _ in named})
        if not matched:
            return []

        value = source.params.get(self._argument) if source is not None else None
        if len(matched) > 1:
            wanted = lookups.normalize_text(value)
            exact = [name for name in matched if lookups.normalize_text(name) == wanted]
            if not exact:
                raise SourceArgAmbiguousWithSuggestions(
                    self._argument, value, matched[: self._max_suggestions]
                )
            target = exact[0]
        else:
            target = matched[0]
        return [record for name, record in named if name == target]

    def _name(self, record: Any) -> str:
        value = self._key(record)
        return "" if value is None else str(value).strip()


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


class PdfMonthColumns(Preprocessor["list[PdfRow]", "tuple[datetime.date, str]"]):
    """Read a months-side-by-side PDF calendar whose columns name their month.

    The sibling of :class:`PdfCalendarColumns` for the other way a printed
    calendar is laid out, and the other way a source can know its geometry.
    Where that one takes the column positions as measurements the source supplies
    and hands back day cells to interpret, this one *finds* the columns from the
    header row that prints the month names, and reads each day cell itself: a
    day number, and whichever round labels are printed beside it::

        parse = parsers.PdfTableParser(min_words=50)
        preprocess = preprocessors.PdfMonthColumns(
            labels=TYPE_MAP, year_pattern=r"Raccolta rifiuti (\\d{4})"
        )
        transform = ICSTransformer(type_value_map=TYPE_MAP)

    Reach for it when the calendar shows a run of months across the page (a
    half-year per sheet is the usual print), which plain text extraction
    collapses into unreadable interleaved lines. Nothing about the page needs
    measuring: the month names are the column anchors, and a run of text belongs
    to the column whose month heading it sits nearest, splitting at the
    midpoints between adjacent headings.

    A page with fewer than two month names in any one row is skipped, since its
    columns cannot be located that way; use :class:`PdfCalendarColumns` for a
    calendar whose blocks are not headed by their month. Everything printed level
    with or above that header row is the sheet's own furniture -- its title, and
    often a tail of the previous December carried over -- so it is ignored rather
    than binned into a column it does not belong to.

    Args:
        labels: the round labels printed in the day cells, matched
            case-insensitively as substrings of the cell, in the order given.
            Pass the transformer's ``type_value_map`` directly.
        read_cell: for a calendar that prints codes rather than names, a
            ``callable(cell_text, source) -> Iterable[str]`` returning the labels
            a dated cell means, used instead of ``labels``. It receives the cell
            exactly as printed (case intact, runs joined by single spaces), and
            it may read ``source.params``, which is what a sheet serving several
            collection tours in one grid needs: the cell says ``B 1``/``B 2`` and
            only the resident's tour applies. Where the columns are, and which
            day a cell is, stay this preprocessor's job either way.
        day_pattern: regex locating the day number in a cell, matched against
            the cell text lowercased, its first group the number. Defaults to a
            day number followed by a three-letter weekday abbreviation, which is
            what a dated cell prints.
        year_pattern: a regex searched against the whole document, its first
            group the four-digit year the calendar is published for. Falls back
            to the current year when unset or unmatched.
    """

    def __init__(
        self,
        *,
        labels: Iterable[str] = (),
        read_cell: "Callable[[str, BaseSource | None], Iterable[str]] | None" = None,
        day_pattern: str = r"(\d{1,2})\s+[a-z]{3}",
        year_pattern: "str | None" = None,
    ):
        self._labels = {str(label).upper(): label for label in labels}
        self._read_cell = read_cell
        if not self._labels and read_cell is None:
            raise ValueError("PdfMonthColumns needs either labels or read_cell")
        self._day_re = re.compile(day_pattern)
        self._year_re = re.compile(year_pattern) if year_pattern else None

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        rows = list(records)
        year = self._document_year(rows)

        for page in sorted({row.page for row in rows}):
            page_rows = [row for row in rows if row.page == page]
            header = self._month_columns(page_rows)
            if header is None:
                continue
            header_y, columns = header
            xs = [x for x, _ in columns]
            months = [month for _, month in columns]
            # A column owns everything up to the midpoint of the gap to the next.
            mids = [(xs[i] + xs[i + 1]) / 2 for i in range(len(xs) - 1)]

            for row in page_rows:
                # The header row and anything above it is the sheet's heading.
                if row.y >= header_y:
                    continue
                cells: dict[int, list[str]] = {}
                for word in row.words:
                    column = sum(1 for mid in mids if word.x0 >= mid)
                    cells.setdefault(column, []).append(word.text)
                for column, texts in cells.items():
                    chunk = " ".join(texts)
                    match = self._day_re.search(chunk.lower())
                    if match is None:
                        continue
                    try:
                        collection_date = datetime.date(
                            year, months[column], int(match.group(1))
                        )
                    except ValueError:
                        continue
                    for label in self._cell_labels(chunk, source):
                        yield collection_date, label

    def _cell_labels(self, chunk: str, source: "BaseSource | None") -> Iterable[str]:
        if self._read_cell is not None:
            return self._read_cell(chunk, source)
        upper_chunk = chunk.upper()
        return [label for upper, label in self._labels.items() if upper in upper_chunk]

    @staticmethod
    def _month_columns(
        page_rows: "list[PdfRow]",
    ) -> "tuple[float, list[tuple[float, int]]] | None":
        """The header row's y, and the (x, month) of each column it names."""
        for row in page_rows:
            found = [
                (word.x0, number)
                for word in row.words
                if (number := recurrence.month(word.text)) is not None
            ]
            if len(found) >= 2:
                return row.y, sorted(found)
        return None

    def _document_year(self, rows: "list[PdfRow]") -> int:
        if self._year_re is not None:
            text = " ".join(word.text for row in rows for word in row.words)
            match = self._year_re.search(text)
            if match:
                return int(match.group(1))
        return datetime.date.today().year


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


def _month_number(value: "str | None") -> "int | None":
    """A month written as a number or as a name in any supported language."""
    text = str(value or "").strip()
    if text.isdigit():
        number = int(text)
        return number if 1 <= number <= 12 else None
    return recurrence.month(text)


class TextDatedBlocks(Preprocessor[str, "tuple[datetime.date, str]"]):
    """Expand a plain-text "a date, then its rounds" schedule into rows.

    The mirror image of :class:`TextGroupedDates`. There, a round's label
    introduces the run of dates it is collected on; here a date heads a block
    and the rounds collected that day are listed beneath it, one per line. That
    is what a per-address schedule printed as a diary looks like, and what a PDF
    generator emits when it renders one day at a time::

        parse = parsers.PdfTextParser(min_chars=100)
        preprocess = preprocessors.TextDatedBlocks(
            block_pattern=(
                r"\\w+\\n(?P<day>\\d+)\\s(?P<month>\\w+)\\n"
                r"(?P<labels>[\\w\\s\\-]+?)(?=\\n\\w+\\n\\d+\\s\\w+|$)"
            ),
            year_pattern=r"Data generowania:\\s(\\d{4})-\\d{2}-\\d{2}",
            normalise=str.capitalize,
        )
        transform = ICSTransformer(type_value_map=TYPE_MAP)

    Such a schedule is nearly always printed without the year, and runs over a
    year boundary if it is long enough. Blocks come out in the document's own
    (chronological) order, so a month earlier than the one before it is the
    calendar turning over: ``roll_year`` reads it that way, which is what keeps
    a December-to-January listing on the right side of New Year.

    A block whose month does not resolve, and a block naming a day that month
    does not have, are skipped rather than failing the fetch.

    Args:
        block_pattern: regex found repeatedly across the document, one match per
            dated block. It must carry the named groups ``day``, ``month`` and
            ``labels``, and may carry ``year`` for a document that dates each
            block in full. ``month`` may be a number or a month name in any
            supported language (:func:`recurrence.month` resolves it, including
            the inflected forms a date reads in, e.g. Polish "lipca").
        label_separator: regex splitting the ``labels`` group into the
            individual round names (default: a newline or a comma).
        normalise: optional ``callable(str) -> str`` applied to each label after
            it is stripped. The transformer matches its ``type_value_map``
            case-insensitively, so this is only needed where the label's case
            survives into the output, i.e. for a round the shared vocabulary
            does not resolve and whose text is therefore preserved verbatim.
        year_pattern: a regex searched against the whole document, its first
            group the four-digit year the schedule starts in. Falls back to the
            current year when unset or unmatched.
        roll_year: whether a month earlier than the previous block's advances
            the year (default True). Turn it off for a document that cannot span
            a year boundary, or one whose blocks are not in date order.
    """

    def __init__(
        self,
        *,
        block_pattern: str,
        label_separator: str = r"[\n,]",
        normalise: "Callable[[str], str] | None" = None,
        year_pattern: "str | None" = None,
        roll_year: bool = True,
    ):
        self._block_re = re.compile(block_pattern)
        missing = {"day", "month", "labels"} - set(self._block_re.groupindex)
        if missing:
            raise ValueError(
                f"block_pattern is missing the named group(s) {sorted(missing)}"
            )
        self._label_re = re.compile(label_separator)
        self._normalise = normalise
        self._year_re = re.compile(year_pattern) if year_pattern else None
        self._roll_year = roll_year

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        text = str(records)
        year = self._document_year(text)
        previous: int | None = None

        for block in self._block_re.finditer(text):
            groups = block.groupdict()
            month = _month_number(groups.get("month"))
            if month is None:
                continue
            if self._roll_year and previous is not None and previous > month:
                year += 1
            previous = month
            try:
                collection_date = datetime.date(
                    int(groups.get("year") or year), month, int(groups["day"])
                )
            except ValueError:
                continue
            for raw in self._label_re.split(groups.get("labels") or ""):
                label = raw.strip()
                if self._normalise is not None:
                    label = self._normalise(label)
                if label:
                    yield collection_date, label

    def _document_year(self, text: str) -> int:
        if self._year_re is not None:
            match = self._year_re.search(text)
            if match:
                return int(match.group(1))
        return datetime.date.today().year


# A calendar grid's own furniture, in any language: a row of nothing but day
# numbers, and a row of nothing but short weekday abbreviations.
_DAY_ROW_PATTERN = r"^(?:\d{1,2})(?:\s+\d{1,2})*$"
_WEEKDAY_ROW_PATTERN = r"^[^\W\d_]{2,3}(?:\s+[^\W\d_]{2,3}){2,}$"


class TextCalendarGrid(Preprocessor[str, "tuple[datetime.date, str]"]):
    """Read a printed month-grid calendar out of a plain-text layer.

    The inverse of :class:`TextGroupedDates`, for the other way a text PDF
    presents a schedule: rather than a round's label introducing its dates, a
    month grid prints the dates and lists the rounds collected under them. The
    text layer comes out as a month heading, a weekday header, then alternating
    day rows and the round names printed in those days' cells::

        parse = parsers.PdfTextParser(min_chars=100)
        preprocess = preprocessors.TextCalendarGrid(
            keys=TYPE_MAP, stop_contains=("your collection schedule",)
        )
        transform = ICSTransformer(type_value_map=TYPE_MAP)

    The binding rule is the one a text extractor gives: the round names that
    follow a day row belong to the highest day number printed on that row. A
    round name is the first word of its line, matched case-insensitively against
    ``keys``; any other line inside the block is ignored, and the block ends at
    the next heading, day row, weekday header or stop phrase.

    Use :class:`~waste_collection_schedule.parsers.PdfTableParser` with
    :class:`PdfMonthColumns` instead when the extractor interleaves the columns
    of a multi-month page, which no line-by-line reading can unpick.

    Args:
        keys: the round names printed in the grid. Pass the transformer's
            ``type_value_map`` directly; its keys are exactly that set.
        stop_contains: phrases that also end a block, matched
            case-insensitively as substrings (a footer or a section title
            printed between the months).
        month_pattern: regex for the month heading, its first group the month
            name (resolved in any supported language) and its second the year.
    """

    def __init__(
        self,
        *,
        keys: Iterable[str],
        stop_contains: Iterable[str] = (),
        month_pattern: str = r"^([^\W\d_]+)\s+(\d{4})$",
    ):
        self._keys = {str(key).upper(): key for key in keys}
        self._stop_contains = tuple(phrase.lower() for phrase in stop_contains)
        self._month_re = re.compile(month_pattern, re.IGNORECASE)
        self._day_row_re = re.compile(_DAY_ROW_PATTERN)
        self._weekday_row_re = re.compile(_WEEKDAY_ROW_PATTERN)

    def _month_heading(self, line: str) -> "tuple[int, int] | None":
        match = self._month_re.match(line)
        if match is None:
            return None
        number = recurrence.month(match.group(1))
        return None if number is None else (number, int(match.group(2)))

    def _is_boundary(self, line: str) -> bool:
        lower = line.lower()
        return (
            self._month_heading(line) is not None
            or bool(self._weekday_row_re.match(line))
            or bool(self._day_row_re.match(line))
            or any(phrase in lower for phrase in self._stop_contains)
        )

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        lines = [line.strip() for line in str(records).splitlines() if line.strip()]
        month = year = None
        index = 0
        while index < len(lines):
            line = lines[index]
            heading = self._month_heading(line)
            if heading is not None:
                month, year = heading
                index += 1
                continue
            if not (month and year and self._day_row_re.match(line)):
                index += 1
                continue

            days = [int(token) for token in line.split() if 1 <= int(token) <= 31]
            found: list[str] = []
            end = index + 1
            while end < len(lines) and not self._is_boundary(lines[end]):
                key = self._keys.get(lines[end].split(" ")[0].upper())
                if key is not None:
                    found.append(key)
                end += 1

            if days and found:
                try:
                    collection_date = datetime.date(year, month, max(days))
                except ValueError:
                    collection_date = None
                if collection_date is not None:
                    for key in found:
                        yield collection_date, key
            index = end


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
