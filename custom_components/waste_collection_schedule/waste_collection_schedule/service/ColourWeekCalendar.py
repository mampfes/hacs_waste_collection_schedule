"""Select a weekday from dated bin-week cells, including printed replacements."""

import calendar
import datetime

from waste_collection_schedule import recurrence
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions


class WeekRows:
    def __init__(self, weekday_param="day", *, holiday="holiday", weekly_keys=()):
        self.weekday_param = weekday_param
        self.holiday = holiday
        self.weekly_keys = weekly_keys

    def __call__(self, records, source=None):
        if source is None:
            raise ValueError("Bin-week calendar requires a source")
        text = source.params[self.weekday_param]
        weekday = recurrence.weekday(text)
        if weekday is None or weekday > 4:
            raise SourceArgumentNotFoundWithSuggestions(
                self.weekday_param, text, list(calendar.day_name)[:5]
            )
        cells = dict(records)
        first, last = min(cells), max(cells)
        start = first.replace(day=1)
        end = last.replace(day=calendar.monthrange(last.year, last.month)[1])
        today = datetime.date.today()
        if not start <= today <= end:
            raise ValueError("The published bin calendar does not cover today")
        for date, key in sorted(cells.items()):
            if date.weekday() != weekday:
                continue
            actual = date
            if key == self.holiday:
                actual = date + datetime.timedelta(days=1)
                key = cells.get(actual)
                if key is None or key == self.holiday:
                    raise ValueError(
                        "Missing printed bin types on the holiday replacement day"
                    )
            if actual < today:
                continue
            yield actual, key
            for additional in self.weekly_keys:
                yield actual, additional
