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
import logging
from typing import Protocol

from dateutil import parser as dateutil_parser

_LOGGER = logging.getLogger(__name__)


class DateParser(Protocol):
    """A callable that parses a date string into a datetime.date.

    The last positional argument is always treated as the date string. This
    lets the same callable be used as a Source attribute and as a transformer
    ``parse_date`` argument.
    """

    def __call__(self, *args: str) -> datetime.date: ...  # noqa: E704


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
