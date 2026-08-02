import datetime

from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Mill Valley Refuse Service"
DESCRIPTION = (
    "Source for Mill Valley Refuse Service (MVRS), Marin County, California, USA."
)
URL = "https://www.millvalleyrefuse.com"

TEST_CASES = {
    "Whole service area": {},
    "With pickup day (Wednesday)": {"pickup_day": "Wednesday"},
    "With pickup day (Tuesday)": {"pickup_day": "Tuesday"},
}

COUNTRY = "us"

# MVRS publishes one alternating-week residential recycling schedule for its
# whole service area as three public Google Calendars, embedded on
# https://www.millvalleyrefuse.com/residential-services . Container recycling
# and paper recycling are collected on alternating weeks (citywide); garbage and
# compost are weekly on each address's normal route day and are not published in
# a machine-readable feed.
RECYCLING_CALENDARS = {
    "Container Recycling": (
        "https://calendar.google.com/calendar/ical/"
        "uokfjeogcqe0daugrn58mvkgo0%40group.calendar.google.com/public/basic.ics"
    ),
    "Paper Recycling": (
        "https://calendar.google.com/calendar/ical/"
        "d5mdlvop2qp45vmstm6gs5p1kg%40group.calendar.google.com/public/basic.ics"
    ),
}
# Office-closure / holiday service notices.
HOLIDAY_CALENDAR = (
    "https://calendar.google.com/calendar/ical/"
    "millvalleyrefuse%40gmail.com/public/basic.ics"
)

ICON_MAP = {
    "Container Recycling": Icons.RECYCLING,
    "Paper Recycling": Icons.PAPER,
}

# Number of days after the Sunday that starts each collection week.
_WEEKDAY_OFFSETS = {
    "Sunday": 0,
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "No address lookup is required. Mill Valley Refuse Service publishes a "
        "single alternating-week recycling schedule for its whole service area "
        "(Mill Valley, Corte Madera, Tiburon, Belvedere, Strawberry and "
        "unincorporated Marin). Optionally set 'pickup_day' to the weekday your "
        "street is serviced so each collection lands on your actual pickup day "
        "instead of the start of the week."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "pickup_day": "Pickup Day",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "pickup_day": (
            "The weekday your address is serviced (e.g. 'Wednesday'). MVRS "
            "collects Monday-Friday depending on your street. If omitted, each "
            "recycling week is marked on the Sunday it begins."
        ),
    }
}


def _weekly_collections(
    dates: list[datetime.date], waste_type: str, offset: int
) -> list[Collection]:
    """Collapse a stream's per-day ICS events into one entry per week.

    MVRS marks each alternating recycling week with all-day calendar events.
    Group every event date by the Sunday that starts its week, then emit a
    single collection per week - shifted by ``offset`` days so it falls on the
    resident's pickup weekday (0 = the week-start Sunday).
    """
    week_starts = {
        # date.isoweekday(): Mon=1 .. Sun=7  ->  Sun%7=0, Mon%7=1, ...
        d - datetime.timedelta(days=d.isoweekday() % 7)
        for d in dates
    }
    return [
        Collection(
            ws + datetime.timedelta(days=offset),
            waste_type,
            icon=ICON_MAP.get(waste_type),
        )
        for ws in sorted(week_starts)
    ]


class Source:
    def __init__(self, pickup_day: str | None = None):
        if pickup_day is not None:
            match = [
                d for d in _WEEKDAY_OFFSETS if d.lower() == pickup_day.strip().lower()
            ]
            if not match:
                raise SourceArgumentNotFoundWithSuggestions(
                    "pickup_day", pickup_day, list(_WEEKDAY_OFFSETS)
                )
            pickup_day = match[0]
        self._pickup_day = pickup_day
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")
        offset = _WEEKDAY_OFFSETS[self._pickup_day] if self._pickup_day else 0
        entries: list[Collection] = []

        for waste_type, url in RECYCLING_CALENDARS.items():
            r = session.get(url)
            r.raise_for_status()
            dates = [d for d, _ in self._ics.convert(r.text)]
            entries.extend(_weekly_collections(dates, waste_type, offset))

        r = session.get(HOLIDAY_CALENDAR)
        r.raise_for_status()
        for d, title in self._ics.convert(r.text):
            icon = Icons.EVENT if "as usual" in title.lower() else Icons.NO_COLLECTION
            entries.append(Collection(d, title, icon=icon))

        return entries
