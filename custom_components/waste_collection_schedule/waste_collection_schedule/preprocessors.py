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
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

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

    def __call__(  # noqa: E704
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
