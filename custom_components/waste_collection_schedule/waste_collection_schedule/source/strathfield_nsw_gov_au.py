import datetime

from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Strathfield Council"
DESCRIPTION = "Source for Strathfield Council, NSW, Australia."
URL = "https://www.strathfield.nsw.gov.au"
TEST_CASES = {
    "Monday collection": {"collection_day": "Monday"},
    "Tuesday collection": {"collection_day": "Tuesday"},
    "Wednesday collection": {"collection_day": "Wednesday"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Organics": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Your collection day is printed on your rates notice. "
        "It can also be found by contacting Strathfield Council."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {"collection_day": "Collection Day"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "collection_day": (
            "The day of the week your bins are collected (e.g. Tuesday). "
            "Check your rates notice or contact Strathfield Council."
        ),
    },
}

# Monday of the first Garden Organics (green lid) week of 2026.
# All Strathfield properties share this fortnightly alternating cycle.
_GREEN_WEEK_ANCHOR = datetime.date(2026, 1, 5)

_WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}


class Source:
    def __init__(self, collection_day: str):
        day = collection_day.strip().lower()
        if day not in _WEEKDAY_MAP:
            raise SourceArgumentNotFoundWithSuggestions(
                "collection_day",
                collection_day,
                [d.capitalize() for d in _WEEKDAY_MAP],
            )
        self._day_offset = _WEEKDAY_MAP[day]

    def fetch(self) -> list[Collection]:
        # Shift the Monday anchor to the user's actual collection weekday
        first_green = _GREEN_WEEK_ANCHOR + datetime.timedelta(days=self._day_offset)
        first_yellow = first_green + datetime.timedelta(weeks=1)

        until = datetime.date.today() + datetime.timedelta(days=730)

        entries = []
        for dt in rrule(WEEKLY, interval=1, dtstart=first_green, until=until):
            entries.append(
                Collection(dt.date(), "General Waste", ICON_MAP["General Waste"])
            )
        for dt in rrule(WEEKLY, interval=2, dtstart=first_green, until=until):
            entries.append(
                Collection(dt.date(), "Garden Organics", ICON_MAP["Garden Organics"])
            )
        for dt in rrule(WEEKLY, interval=2, dtstart=first_yellow, until=until):
            entries.append(Collection(dt.date(), "Recycling", ICON_MAP["Recycling"]))
        return entries
