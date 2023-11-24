import datetime
import logging
import re

import icalendar
import recurring_ical_events
import jinja2


_LOGGER = logging.getLogger(__name__)


class ICS_v1:
    def __init__(
        self,
        offset=None,
        regex=None,
        split_at=None,
        title_template="{{date.summary}}",
    ):
        self._offset = offset
        self._regex = None
        if regex is not None:
            self._regex = re.compile(regex)
        self._split_at = split_at

        self._title_template = title_template

    def convert(self, ics_data):
        # parse ics file
        calendar = icalendar.Calendar.from_ical(ics_data)

        # calculate start- and end-date for recurring events
        start_date = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if self._offset is not None:
            start_date -= datetime.timedelta(days=self._offset)
        end_date = start_date.replace(year=start_date.year + 1)

        events = recurring_ical_events.of(calendar).between(start_date, end_date)

        entries = []
        for e in events:
            if e.name == "VEVENT":
                # calculate date
                dtstart = None
                if type(e.get("dtstart").dt) == datetime.date:
                    dtstart = e.get("dtstart").dt
                elif type(e.get("dtstart").dt) == datetime.datetime:
                    dtstart = e.get("dtstart").dt.date()
                if self._offset is not None:
                    dtstart += datetime.timedelta(days=self._offset)

                # calculate waste type
                environment = jinja2.Environment()
                title_template = environment.from_string(self._title_template)
                entry_title = title_template.render(date=e)

                if self._regex is not None:
                    match = self._regex.match(entry_title)
                    if match:
                        entry_title = match.group(1)

                if self._split_at is not None:
                    entry_title = re.split(self._split_at, entry_title)
                    for t in entry_title:
                        entries.append((dtstart, t.strip().title()))
                else:
                    entries.append((dtstart, entry_title))

        return entries
