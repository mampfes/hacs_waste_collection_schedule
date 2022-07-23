from dateutil.rrule import rrule
import datetime
from dateutil import parser

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
}

FREQNAMES = ["YEARLY", "MONTHLY", "WEEKLY", "DAILY"]


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
    ):
        self._type = type
        self._dates = [parser.isoparse(d).date() for d in dates or []]

        self._recurrence = FREQNAMES.index(frequency) if frequency is not None else None
        self._interval = interval
        self._start = parser.isoparse(start).date() if start else None
        self._until = parser.isoparse(until).date() if until else None
        self._excludes = [parser.isoparse(d).date() for d in excludes or []]

    def fetch(self):
        dates = []

        if self._recurrence is not None:
            ruledates = rrule(
                freq=self._recurrence,
                interval=self._interval,
                dtstart=self._start,
                until=self._until,
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
