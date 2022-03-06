import datetime
import logging
import re

from icalevents import icalevents

_LOGGER = logging.getLogger(__name__)


class ICS:
    def __init__(self, offset=None, regex=None, split_at=None):
        self._offset = offset
        self._regex = None
        if regex is not None:
            self._regex = re.compile(regex)
        self._split_at = split_at

    def convert(self, ics_data):
        # calculate start- and end-date for recurring events
        start_date = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if self._offset is not None:
            start_date -= datetime.timedelta(days=self._offset)
        end_date = start_date.replace(year=start_date.year + 1)

        # parse ics data
        events = icalevents.events(
            start=start_date, end=end_date, string_content=ics_data.encode()
        )

        entries = []
        for e in events:
            # calculate date
            dtstart = None
            if type(e.start) == datetime.date:
                dtstart = e.start
            elif type(e.start) == datetime.datetime:
                dtstart = e.start.date()
            if self._offset is not None:
                dtstart += datetime.timedelta(days=self._offset)

            # calculate waste type
            summary = str(e.summary)
            if self._regex is not None:
                match = self._regex.match(summary)
                if match:
                    summary = match.group(1)

            if self._split_at is not None:
                summary = re.split(self._split_at, summary)
                for t in summary:
                    entries.append((dtstart, t.strip().title()))
            else:
                entries.append((dtstart, summary))

        return entries
