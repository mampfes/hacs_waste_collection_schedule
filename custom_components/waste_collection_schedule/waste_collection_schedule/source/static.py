from dateutil.rrule import rrule
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

import datetime
from dateutil import parser
from typing import Dict

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Static Source"
DESCRIPTION = "Source for static waste collection schedules."
URL = None
TEST_CASES = {
    "Dates only": {"type": "Dates only", "dates": {"2022-01-01", "2022-02-28"}},
    "Same date twice": {"type": "Dates only", "dates": {"2022-01-01", "2022-01-01"}},
    "Recurrence only": {
        "type": "Recurrence only",
        "frequency": "MONTHLY",
        "interval": 1,
        "start": "2022-01-01",
        "until": "2022-12-31",
    },
    "Recurrence with exception": {
        "type": "Recurrence with exception",
        "frequency": "MONTHLY",
        "interval": 1,
        "start": "2022-01-01",
        "until": "2022-12-31",
        "excludes": {"2022-01-01"},
        "dates": {"2022-01-02"},
    },
    "Recurrence with Weekday and count": {
        "type": "Recurrence with Weekday",
        "frequency": "MONTHLY",
        "start": "2022-01-01",
        "until": "2022-12-31",
        "weekdays": {"MO": 1, 1: 2},
    },
    "Recurrence with Weekday without count": {
        "type": "Recurrence with Weekday without count",
        "frequency": "MONTHLY",
        "start": "2022-01-01",
        "until": "2022-12-31",
        "weekdays": {"MO",5},
    },
    "Recurrence with Weekday with and without count": {
        "type": "Recurrence with Weekday with and without count",
        "frequency": "MONTHLY",
        "start": "2022-01-01",
        "until": "2022-12-31",
        "weekdays": {"SA":-1,"MO":None,"TU":"Every"},
    },
}

FREQNAMES = ["YEARLY", "MONTHLY", "WEEKLY", "DAILY"]
WEEKDAYNAME = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
WEEKDAYS = [MO, TU, WE, TH, FR, SA, SU]

class Source:
    def __init__(
        self,
        type: str,
        dates: list[str] = None,
        frequency: str = None,
        interval: int = 1,
        start: datetime.date = None,
        until: datetime.date = None,
        excludes: list[str] = None,
        weekdays: list[str|int] | dict[str|int,int|str|None] = None,
    ):
        self._weekdays = None
        if (weekdays is not None):
            self._weekdays = []
            if (isinstance(weekdays, dict)):
                for weekday, count in weekdays.items():
                    print(weekday, count)
                    weekday_index = None
                    if (isinstance(weekday, int)):
                        weekday_index = weekday
                    elif (isinstance(weekday, str)):
                        weekday_index = WEEKDAYNAME.index(weekday)
                    
                    if (weekday_index>6 or weekday_index<0):
                        continue
                    
                    if (isinstance(count, str)):
                       count = int(count) if count.isdigit() else "every"
                    
                    if (count is None or count == "every" ):
                        [self._weekdays.append(WEEKDAYS[weekday_index](x)) for x in range(1,7)]
                        continue
                    
                    self._weekdays.append(WEEKDAYS[weekday_index](count))
                
            else:
                for weekday in weekdays or []:
                    if (isinstance(weekday, int)):
                        self._weekdays.append(weekday)
                    if (isinstance(weekday, str)):
                        self._weekdays.append(WEEKDAYNAME.index(weekday))
            if self._weekdays == []: self._weekdays = None
                
        self._type = type
        self._dates = [parser.isoparse(d).date() for d in dates or []]

        self._recurrence = FREQNAMES.index(frequency) if frequency is not None else None
        self._interval = interval
        self._start = parser.isoparse(start).date() if start else None
        self._until = parser.isoparse(until).date() if until else None
        self._excludes = [parser.isoparse(d).date() for d in excludes or []]

    def fetch(self):
        dates = []

        print(self._weekdays)
        if self._recurrence is not None:
            ruledates = rrule(
                freq=self._recurrence,
                interval=self._interval,
                dtstart=self._start,
                until=self._until,
                byweekday=self._weekdays,
            )

            for ruleentry in ruledates:
                date = ruleentry.date()

                if self._excludes is not None and date in self._excludes:
                    continue

                dates.append(date)

        if self._dates is not None:
            dates.extend(self._dates)

        dates.sort()

        entries = [Collection(date, self._type) for date in set(dates)]
        return entries
