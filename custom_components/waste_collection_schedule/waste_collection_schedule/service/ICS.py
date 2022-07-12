import datetime
import logging
import re
from typing import Any, List, Optional, Tuple

from icalevents import icalevents

_LOGGER = logging.getLogger(__name__)


class ICS:
    def __init__(
        self,
        offset: Optional[int] = None,
        regex: Optional[str] = None,
        split_at: Optional[str] = None,
    ):
        self._offset = offset
        self._regex = None
        self._split_at = None

        if regex is not None:
            self._regex = re.compile(regex)

        if split_at is not None:
            self._split_at = re.compile(split_at)

    def convert(self, ics_data: str) -> List[Tuple[datetime.date, str]]:
        # calculate start- and end-date for recurring events
        start_date = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if self._offset is not None:
            start_date -= datetime.timedelta(days=self._offset)
        end_date = start_date.replace(year=start_date.year + 1)

        # parse ics data
        events: List[Any] = icalevents.events(
            start=start_date, end=end_date, string_content=ics_data.encode()
        )

        entries: List[Tuple[datetime.date, str]] = []

        for e in events:
            # calculate date
            dtstart: Optional[datetime.date] = None

            if isinstance(e.start, datetime.datetime):
                dtstart = e.start.date()
            elif isinstance(e.start, datetime.date):
                dtstart = e.start

            # Only continue if a start date can be found in the entry
            if dtstart is not None:
                if self._offset is not None:
                    dtstart += datetime.timedelta(days=self._offset)

                # calculate waste type
                summary = str(e.summary)

                if self._regex is not None:
                    if match := self._regex.match(summary):
                        summary = match.group(1)

                if self._split_at is not None:
                    summary = re.split(self._split_at, summary)
                    entries.extend((dtstart, t.strip().title()) for t in summary)
                else:
                    entries.append((dtstart, summary))

        return entries
