"""Date parsing utilities.

Each parser is a function that takes a string and returns a datetime.date.
Sources select a parser by format or use the auto-detect fallback.
"""

import datetime
import logging

from dateutil import parser as dateutil_parser

_LOGGER = logging.getLogger(__name__)


def auto(*args) -> datetime.date:
    """Auto-detect date format using dateutil.

    Works both as a bound method (``parse_date = date_parsers.auto`` on a
    Source class, called as ``self.parse_date(date_str)``) and as a plain
    callable (passed to a transformer as ``parse_date=date_parsers.auto``).
    The last positional argument is always treated as the date string.
    """
    date_str = args[-1]
    return dateutil_parser.parse(str(date_str).strip()).date()


def for_format(fmt: str):
    """Return a date parser for a specific strptime format.

    Works both as a bound method (``parse_date = date_parsers.for_format(fmt)``
    on a Source class) and as a plain callable passed to a transformer
    (``parse_date=date_parsers.for_format(fmt)``).
    The last positional argument is always treated as the date string.
    """

    def _parse(*args) -> datetime.date:
        date_str = args[-1]
        return datetime.datetime.strptime(str(date_str).strip(), fmt).date()

    return _parse
