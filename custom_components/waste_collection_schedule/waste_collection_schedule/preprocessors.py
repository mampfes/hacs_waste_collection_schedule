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

import datetime
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeVar

from bs4 import Tag

from waste_collection_schedule import recurrence

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

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
