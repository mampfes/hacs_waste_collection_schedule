"""Date parsing utilities.

Each parser is a typed callable that takes one or more positional arguments
and returns a datetime.date. The last positional argument is always treated
as the date string, so a parser works equally well as a bound source attribute
(``self.parse_date(date_str)``) or passed to a transformer
(``parse_date=date_parsers.auto``).

Ergonomic module aliases are provided::

    parse_date = date_parsers.auto            # DateParserAuto instance
    parse_date = date_parsers.for_format(fmt) # DateParserForFormat factory
"""

import datetime
from typing import Protocol

from dateutil import parser as dateutil_parser


class DateParser(Protocol):
    """A callable that parses a date string into a datetime.date.

    The last positional argument is always treated as the date string. This
    lets the same callable be used as a Source attribute and as a transformer
    ``parse_date`` argument.
    """

    def __call__(self, *args: str) -> datetime.date: ...


class DateParserAuto(DateParser):
    """Auto-detect date format using dateutil.

    The last positional argument is always treated as the date string.
    """

    def __call__(self, *args: str) -> datetime.date:
        date_str = args[-1]
        return dateutil_parser.parse(str(date_str).strip()).date()


class DateParserForFormat(DateParser):
    """Parse date strings in a specific format using datetime.strptime.

    Prefer the ``for_format(fmt)`` factory, which returns a configured
    instance. The last positional argument is always treated as the date
    string.
    """

    def __init__(self, fmt: str):
        self.fmt = fmt

    def __call__(self, *args: str) -> datetime.date:
        date_str = args[-1]
        return datetime.datetime.strptime(str(date_str).strip(), self.fmt).date()


class DateParserFromEpoch(DateParser):
    """Parse a Unix timestamp into a date.

    Accepts an int or numeric string (JSON APIs often return seconds, or
    milliseconds for JavaScript ``Date`` values). The last positional argument
    is the timestamp. The timestamp is interpreted in ``tz`` (UTC by default,
    deterministic) so the resulting calendar date does not depend on the host's
    local timezone.
    """

    def __init__(
        self,
        unit: str = "s",
        tz: datetime.timezone = datetime.timezone.utc,
    ):
        if unit not in ("s", "ms"):
            raise ValueError("unit must be 's' (seconds) or 'ms' (milliseconds)")
        self.unit = unit
        self.tz = tz

    def __call__(self, *args: str) -> datetime.date:
        seconds = float(args[-1])
        if self.unit == "ms":
            seconds /= 1000.0
        return datetime.datetime.fromtimestamp(seconds, tz=self.tz).date()


class DateParserNextWeekday(DateParser):
    """Resolve a date string with no year to its next on/after-today occurrence.

    For providers that publish a collection date without a year because it's
    always in the near future -- either:

    * a bare weekday name (``"Monday"``) -- resolved via the shared
      multilingual ``recurrence.weekday()`` lookup, returning the next
      occurrence of that weekday; or
    * a ``fmt`` with no ``%Y`` (e.g. ``"%A %d %B"`` for ``"Friday 10 July"``)
      -- parsed via ``strptime`` for the month/day, then rolled to whichever
      of this year / next year puts the result on or after today (or
      ``on_or_after``).

    The last positional argument is always treated as the date string.
    """

    def __init__(
        self,
        fmt: "str | None" = None,
        *,
        on_or_after: "datetime.date | None" = None,
    ):
        if fmt is not None and "%Y" in fmt:
            raise ValueError("next_weekday's fmt must not include a year (%Y)")
        self.fmt = fmt
        self.on_or_after = on_or_after

    def __call__(self, *args: str) -> datetime.date:
        from waste_collection_schedule import recurrence

        date_str = str(args[-1]).strip()
        base = self.on_or_after or datetime.date.today()

        if self.fmt is None or self.fmt.strip() in ("%A", "%a"):
            weekday = recurrence.weekday(date_str)
            if weekday is None:
                raise ValueError(f"Unrecognised weekday name: {date_str!r}")
            return recurrence.next_weekday(weekday, on_or_after=base)

        parsed = datetime.datetime.strptime(date_str, self.fmt)
        for year in (base.year, base.year + 1):
            try:
                candidate = parsed.replace(year=year).date()
            except ValueError:
                continue  # e.g. 29 February in a non-leap year
            if candidate >= base:
                return candidate
        # Shouldn't normally be reached (next year's candidate is always >=
        # base), but fall back to this year's date rather than raising.
        return parsed.replace(year=base.year).date()


# Ergonomic module-level aliases.
auto = DateParserAuto()


def for_format(fmt: str) -> DateParserForFormat:
    """Return a DateParserForFormat for a specific strptime format."""
    return DateParserForFormat(fmt)


def from_epoch(
    unit: str = "s",
    tz: datetime.timezone = datetime.timezone.utc,
) -> DateParserFromEpoch:
    """Return a DateParser for Unix timestamps (``unit`` is ``"s"`` or ``"ms"``)."""
    return DateParserFromEpoch(unit=unit, tz=tz)


def next_weekday(
    fmt: "str | None" = None,
    *,
    on_or_after: "datetime.date | None" = None,
) -> DateParserNextWeekday:
    """Return a DateParser resolving a year-less date to its next occurrence.

    Pass no ``fmt`` (or ``"%A"``/``"%a"``) for a bare weekday name; pass a
    ``strptime`` format with no ``%Y`` (e.g. ``"%A %d %B"``) for a
    weekday-plus-day-plus-month string. See :class:`DateParserNextWeekday`.
    """
    return DateParserNextWeekday(fmt, on_or_after=on_or_after)
