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


# Ergonomic module-level aliases.
auto = DateParserAuto()


def for_format(fmt: str) -> DateParserForFormat:
    """Return a DateParserForFormat for a specific strptime format."""
    return DateParserForFormat(fmt)
