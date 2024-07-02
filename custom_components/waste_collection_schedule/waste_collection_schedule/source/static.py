import datetime
import logging
from collections import OrderedDict

from dateutil import parser
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, rrule, weekday
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Static Source"
DESCRIPTION = "Source for static waste collection schedules."
URL = None
TEST_CASES = {
    "Dates only": {"type": "Dates only", "dates": ["2022-01-01", "2022-02-28"]},
    "Same date twice": {"type": "Dates only", "dates": ["2022-01-01", "2022-01-01"]},
    "Recurrence monthly by date": {
        "type": "First day of month",
        "frequency": "MONTHLY",
        "interval": 1,
        "start": "2022-01-01",
        "until": "2022-12-31",
    },
    "Recurrence monthly by date with date list": {
        "type": "First day of month excluding 01-Jan, including 02-Jan",
        "frequency": "MONTHLY",
        "interval": 1,
        "start": "2022-01-01",
        "until": "2022-12-31",
        "excludes": ["2022-01-01"],
        "dates": ["2022-01-02"],
    },
    "Recurrence with weekday dict (day + byweekday)": {
        "type": "First Monday and second Tuesday of the month",
        "frequency": "MONTHLY",
        "start": "2022-01-01",
        "weekdays": {"MO": 1, "TU": 2},
    },
    "Recurrence with first Saturday of the month": {
        "type": "First Saturday of the month",
        "frequency": "MONTHLY",
        "start": "2022-01-01",
        "weekdays": "SA",
    },
    "Recurrence with last Saturday of the month": {
        "type": "Last Saturday of the month",
        "frequency": "MONTHLY",
        "start": "2022-01-01",
        "weekdays": {"SA": -1},
    },
    "Recurrence weekly specified by weekday": {
        "type": "Every Friday",
        "frequency": "WEEKLY",
        "weekdays": "FR",
    },
}

FREQNAMES = ["YEARLY", "MONTHLY", "WEEKLY", "DAILY"]
WEEKDAY_MAP = {"MO": MO, "TU": TU, "WE": WE, "TH": TH, "FR": FR, "SA": SA, "SU": SU}
_LOGGER = logging.getLogger(__name__)


def validate_params(user_input):
    errors = {}
    if not (weekdays := user_input.get("weekdays")):
        return errors

    if isinstance(weekdays, str):
        if weekdays not in WEEKDAY_MAP:
            errors["weekdays"] = "invalid_weekday"
        return errors

    if not isinstance(weekdays, dict):
        for wday, count in weekdays.items():
            if wday not in WEEKDAY_MAP:
                errors["weekdays"] = "invalid_weekday"
                break
            if not isinstance(count, int):
                errors["weekdays"] = "invalid_count"
                break
        return errors
    errors["weekdays"] = "invalid_weekdays"
    return errors


CONFIG_FLOW_TYPES = {
    "frequency": {
        "type": "SELECT",
        "values": [f.lower() for f in FREQNAMES],
        "multiple": False,
    }
}


def check_dates(dates):
    if not isinstance(dates, list):
        return False

    for date in dates:
        try:
            parser.isoparse(date)
        except ValueError:
            return False

    return True


def check_date(date):
    try:
        parser.isoparse(date)
    except ValueError:
        return False
    return True


def get_tyep(params):
    return type(params)


class Source:
    def __init__(
        self,
        type: str,
        dates: list[datetime.date | str] | None = None,
        frequency: str | None = None,
        interval: int = 1,
        start: datetime.date | str | None = None,
        until: datetime.date | str | None = None,
        count: int | None = None,
        excludes: list[datetime.date | str] | None = None,
        weekdays: str | dict[str | int, int | str | None] | None = None,
    ):
        for d in dates or []:
            _LOGGER.debug(f"date: {d}")
            _LOGGER.debug(f"date type: {get_tyep(d)}")

        self._weekdays: list[weekday] | None = None
        if weekdays is not None:
            self._weekdays = []
            if isinstance(weekdays, dict | OrderedDict):
                [
                    self.add_weekday(
                        weekday,
                        int(number) if number is not None and number != "" else 1,
                    )
                    for weekday, number in weekdays.items()
                ]

            elif isinstance(weekdays, str):
                self.add_weekday(weekdays, 1)

            else:
                raise Exception(f"Invalid weekdays format: {weekdays}")

            if self._weekdays == []:
                self._weekdays = None

        self._type = type
        self._dates = [
            d if isinstance(d, datetime.date) else parser.isoparse(d).date()
            for d in dates or []
        ]

        frequency = frequency.upper() if frequency else None
        self._recurrence = FREQNAMES.index(frequency) if frequency is not None else None
        self._interval = interval
        self._start = (
            start
            if isinstance(start, datetime.date)
            else parser.isoparse(start).date()
            if start
            else None
        )
        if until:
            self._until: datetime.date | None = (
                until
                if isinstance(until, datetime.date)
                else parser.isoparse(until).date()
            )
            self._count = None
        else:
            self._until = None
            self._count = count if count else 10
        self._excludes = [
            d if isinstance(d, datetime.date) else parser.isoparse(d).date()
            for d in excludes or []
        ]

    def add_weekday(self, weekday, count: int):
        if self._weekdays is None:
            raise ValueError("Internal Error: weekdays not initialized")

        if weekday not in WEEKDAY_MAP:
            raise Exception(f"invalid weekday: {weekday}")

        self._weekdays.append(WEEKDAY_MAP[weekday](count))

    def fetch(self):
        dates = []

        if self._recurrence is not None:
            ruledates = rrule(
                freq=self._recurrence,
                interval=self._interval,
                dtstart=self._start,
                until=self._until,
                count=self._count,
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
