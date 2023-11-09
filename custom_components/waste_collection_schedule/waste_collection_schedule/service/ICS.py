import datetime
import logging
import re
from typing import Any, List, Optional, Tuple

import jinja2
from icalevents import icalevents

_LOGGER = logging.getLogger(__name__)


class ICS:
    def __init__(
        self,
        offset: Optional[int] = None,
        regex: Optional[str] = None,
        split_at: Optional[str] = None,
        title_template: Optional[str] = "{{date.summary}}",
    ):
        self._offset = offset
        self._regex = None
        self._split_at = None

        if regex is not None:
            self._regex = re.compile(regex)

        if split_at is not None:
            self._split_at = re.compile(split_at)

        self._title_template = title_template

    def convert(self, ics_data: str) -> List[Tuple[datetime.date, str]]:
        # calculate start- and end-date for recurring events
        start_date = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if self._offset is not None:
            start_date -= datetime.timedelta(days=self._offset)
        end_date = start_date.replace(year=start_date.year + 1)

        ics_data = re.sub(
            r"(EXDATE;VALUE=DATE:[0-9]+)\r?\n",
            lambda m: m.group(1) + "T010000\n",
            ics_data,
        )

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

                environment = jinja2.Environment()
                title_template = environment.from_string(self._title_template)
                entry_title = title_template.render(date=e)

                if self._regex is not None:
                    match = self._regex.match(entry_title)
                    if match:
                        entry_title = match.group(1)

                if self._split_at is not None:
                    entry_title = re.split(self._split_at, entry_title)
                    entries.extend((dtstart, t.strip().title()) for t in entry_title)
                else:
                    entries.append((dtstart, entry_title))

        return entries
