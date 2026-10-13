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
import re
import zoneinfo
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
        tz: datetime.tzinfo = datetime.UTC,
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


class DateParserInCurrentYear(DateParser):
    """Parse a year-less date as falling in the current calendar year.

    For a provider that publishes this year's whole schedule without a year
    ("6/2, 20/2, 6/3"), where the past dates are genuinely past rather than
    next year's: :class:`DateParserNextWeekday` would roll them forward and
    invent a second year of collections. Prefer the ``in_current_year(fmt)``
    factory. The year is appended before parsing, so 29 February parses in a
    leap year.
    """

    def __init__(self, fmt: str):
        if "%Y" in fmt:
            raise ValueError("in_current_year's fmt must not include a year (%Y)")
        self.fmt = fmt

    def __call__(self, *args: str) -> datetime.date:
        date_str = str(args[-1]).strip()
        year = datetime.date.today().year
        return datetime.datetime.strptime(f"{date_str} {year}", f"{self.fmt} %Y").date()


class DateParserNearestYear(DateParser):
    """Parse a year-less date into whichever year puts it nearest today.

    For the "your next collections" page that lists a few dates around today
    without a year ("Mon 28 September"): the list crosses the new year in
    December, and it may still show the collection that ran yesterday.
    :class:`DateParserInCurrentYear` gets the first wrong (January lands in the
    past), :class:`DateParserNextWeekday` the second (yesterday lands a year
    ahead). Picking the candidate year that is closest to today gets both
    right, for any page that shows dates within about six months of today.
    Prefer the ``nearest_year(fmt)`` factory.
    """

    def __init__(self, fmt: str):
        if "%Y" in fmt:
            raise ValueError("nearest_year's fmt must not include a year (%Y)")
        self.fmt = fmt

    def __call__(self, *args: str) -> datetime.date:
        date_str = str(args[-1]).strip()
        today = datetime.date.today()
        candidates = []
        for year in (today.year - 1, today.year, today.year + 1):
            try:
                candidates.append(
                    datetime.datetime.strptime(
                        f"{date_str} {year}", f"{self.fmt} %Y"
                    ).date()
                )
            except ValueError:
                continue  # 29 February outside a leap year
        if not candidates:
            raise ValueError(f"{date_str!r} does not match {self.fmt!r}")
        return min(candidates, key=lambda candidate: abs(candidate - today))


class DateParserNamedMonth(DateParser):
    """Parse a day, a month *name* and a year, in any supported language.

    For "Tisdag 4 juni 2024", "4. Juni 2024" or "wtorek, 4 czerwca 2024": an
    optional leading weekday is ignored, the month name resolves through
    :func:`recurrence.month` (so no per-source month table). Prefer the
    ``named_month()`` factory.
    """

    _PATTERN = re.compile(r"(\d{1,2})\.?\s+([^\W\d_]+)\.?,?\s+(\d{4})")

    def __call__(self, *args: str) -> datetime.date:
        from . import recurrence

        date_str = str(args[-1]).strip()
        match = self._PATTERN.search(date_str)
        month = recurrence.month(match.group(2)) if match else None
        if match is None or month is None:
            raise ValueError(f"{date_str!r} is not a day, month name and year")
        return datetime.date(int(match.group(3)), month, int(match.group(1)))


class DateParserIsoWeek(DateParser):
    """Parse a calendar week ("v10 2025", "KW 10 2025") to that week's Monday.

    A week range ("v27 - v28 2025") resolves to the start of its first week.
    Weeks are ISO 8601 weeks, which is how week numbers are printed. Prefer
    the ``iso_week()`` factory.
    """

    _PATTERN = re.compile(
        r"^[^\W\d_]{1,4}\.?\s*(\d{1,2})(?:\s*-\s*[^\W\d_]{0,4}\.?\s*\d{1,2})?\s+(\d{4})$"
    )

    def __call__(self, *args: str) -> datetime.date:
        date_str = str(args[-1]).strip()
        match = self._PATTERN.match(date_str)
        if match is None:
            raise ValueError(f"{date_str!r} is not a calendar week and year")
        return datetime.date.fromisocalendar(
            int(match.group(2)), int(match.group(1)), 1
        )


class DateParserFirstOf(DateParser):
    """Try several parsers in turn, for a field that mixes date notations."""

    def __init__(self, *parsers: DateParser):
        self.parsers = parsers

    def __call__(self, *args: str) -> datetime.date:
        for parser in self.parsers:
            try:
                return parser(*args)
            except ValueError:
                continue
        raise ValueError(f"{args[-1]!r} matches none of the accepted date formats")


class DateParserInZone(DateParser):
    """Read an ISO 8601 timestamp as the calendar date it falls on in a zone.

    For an API that stamps a collection with an instant (``2026-10-14T22:00:00Z``)
    where the day it means is the one on the clock in the provider's own
    time zone (15 October in Copenhagen). ``DateParserAuto`` would keep the UTC
    date, which is a day off for every instant in the zone's first hours. A
    timestamp with no offset is taken to be in the zone already. Prefer the
    ``in_timezone(zone)`` factory. The last positional argument is the string.
    """

    def __init__(self, zone: str):
        self.zone = zoneinfo.ZoneInfo(zone)

    def __call__(self, *args: str) -> datetime.date:
        stamp = dateutil_parser.isoparse(str(args[-1]).strip())
        if stamp.tzinfo is None:
            return stamp.date()
        return stamp.astimezone(self.zone).date()


# Ergonomic module-level aliases.
auto = DateParserAuto()


def for_format(fmt: str) -> DateParserForFormat:
    """Return a DateParserForFormat for a specific strptime format."""
    return DateParserForFormat(fmt)


def from_epoch(
    unit: str = "s",
    tz: datetime.tzinfo = datetime.UTC,
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


def in_current_year(fmt: str) -> DateParserInCurrentYear:
    """Return a DateParser placing a year-less date in the current year.

    See :class:`DateParserInCurrentYear`; use :func:`next_weekday` instead when
    the provider lists only upcoming dates.
    """
    return DateParserInCurrentYear(fmt)


def nearest_year(fmt: str) -> DateParserNearestYear:
    """Return a DateParser placing a year-less date in the year nearest today.

    See :class:`DateParserNearestYear`: for a short list of dates around today
    that may include the one just past and may cross the new year.
    """
    return DateParserNearestYear(fmt)


def named_month() -> DateParserNamedMonth:
    """Return a DateParser for "<weekday> 4 <month name> 2024" in any language."""
    return DateParserNamedMonth()


def iso_week() -> DateParserIsoWeek:
    """Return a DateParser for a calendar week ("v10 2025") as its Monday."""
    return DateParserIsoWeek()


def first_of(*parsers: DateParser) -> DateParserFirstOf:
    """Return a DateParser trying each of ``parsers`` until one accepts."""
    return DateParserFirstOf(*parsers)


def in_timezone(zone: str) -> DateParserInZone:
    """Return a DateParser giving the date an ISO timestamp falls on in ``zone``."""
    return DateParserInZone(zone)


class DateParserRelativeWords(DateParser):
    """Resolve "Today" / "Tomorrow" itself and hand every other date on.

    For a "your next collections" list that prints the nearest days as words
    instead of dates ("Tomorrow", then "Fri 16th Oct"). The word is matched
    case-insensitively against ``words`` (a name to day-offset mapping) and
    resolved relative to today; anything else goes to ``fallback``. Prefer the
    ``relative_words(fallback)`` factory.
    """

    def __init__(
        self,
        fallback: DateParser,
        words: "dict[str, int] | None" = None,
    ):
        self.fallback = fallback
        self.words = {
            word.casefold(): offset
            for word, offset in (words or {"today": 0, "tomorrow": 1}).items()
        }

    def __call__(self, *args: str) -> datetime.date:
        offset = self.words.get(str(args[-1]).strip().casefold())
        if offset is None:
            return self.fallback(*args)
        return datetime.date.today() + datetime.timedelta(days=offset)


class DateParserWithoutOrdinals(DateParser):
    """Drop the English ordinal suffix before parsing ("Fri 16th Oct").

    ``strptime`` has no directive for "16th"; this removes the ``st``/``nd``/
    ``rd``/``th`` that follows a day number and hands the rest to ``fallback``.
    Prefer the ``without_ordinals(fallback)`` factory.
    """

    _ORDINAL = re.compile(r"(?<=\d)(?:st|nd|rd|th)\b", re.IGNORECASE)

    def __init__(self, fallback: DateParser):
        self.fallback = fallback

    def __call__(self, *args: str) -> datetime.date:
        cleaned = self._ORDINAL.sub("", str(args[-1]))
        return self.fallback(*args[:-1], cleaned)


def relative_words(
    fallback: DateParser, words: "dict[str, int] | None" = None
) -> DateParserRelativeWords:
    """Return a DateParser resolving "Today"/"Tomorrow", else using ``fallback``.

    See :class:`DateParserRelativeWords`.
    """
    return DateParserRelativeWords(fallback, words)


def without_ordinals(fallback: DateParser) -> DateParserWithoutOrdinals:
    """Return a DateParser stripping "st"/"nd"/"rd"/"th" before ``fallback``.

    See :class:`DateParserWithoutOrdinals`.
    """
    return DateParserWithoutOrdinals(fallback)
