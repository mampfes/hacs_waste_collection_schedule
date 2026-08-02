import math
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "City of Tallahassee"
DESCRIPTION = "Source for City of Tallahassee, FL waste, recycling and bulky item/yard waste collection."
URL = "https://www.talgov.com/you/swslookup"
COUNTRY = "us"

TEST_CASES = {
    "400 S Monroe St": {"address": "400 S Monroe St"},
    "2001 Trescott Dr (Red Thursday bulk)": {"address": "2001 Trescott Dr"},
    "1004 Piney Z Plantation Rd (Blue Friday bulk)": {
        "address": "1004 Piney Z Plantation Rd"
    },
}

ICON_MAP = {
    "Garbage/Recycling": Icons.GENERAL_WASTE,
    "Bulky Items/Yard Waste": Icons.BULKY,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address as shown in the City of Tallahassee lookup tool (e.g. '400 S Monroe St')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

ADDRESS_URL = "https://handlersp.talgov.com/autosuggest/UtilSWAddressListUmax.ashx"
SCHEDULE_URL = "https://handlersp.talgov.com/solidwaste/UtilSWRedBlueUmax.ashx"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

GARBAGE_RECYCLING = "Garbage/Recycling"
BULKY_YARD_WASTE = "Bulky Items/Yard Waste"

# How many weeks ahead to project the weekly garbage/recycling schedule.
WEEKLY_WEEKS_AHEAD = 26

# How many weeks ahead to scan for the biweekly Red/Blue bulky/yard waste
# schedule (produces roughly half as many actual collection dates).
BULK_WEEKS_AHEAD = 52


def _normalize(address: str) -> str:
    return " ".join(address.split()).strip().lower()


def _week_color(d: date) -> str:
    """Replicate the Red/Blue week calculation used by talgov.com's own
    client-side script (see the `RedBlueWeek` logic on
    https://www.talgov.com/you/swslookup): a simple (non-ISO) week-of-year
    count where week 1 is always "Red".
    """
    year_start = date(d.year, 1, 1)
    days_diff = (d - year_start).days
    # JavaScript's Date.getDay(): Sunday=0 ... Saturday=6.
    js_year_start_weekday = (year_start.weekday() + 1) % 7
    week_no = math.ceil((days_diff + js_year_start_weekday + 1) / 7)
    return "Red" if week_no % 2 == 0 else "Blue"


def _weekly_dates(weekday: int, waste_type: str) -> list[Collection]:
    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7
    first = today + timedelta(days=days_ahead)
    icon = ICON_MAP.get(waste_type)
    return [
        Collection(date=first + timedelta(weeks=i), t=waste_type, icon=icon)
        for i in range(WEEKLY_WEEKS_AHEAD)
    ]


def _biweekly_dates(weekday: int, color: str, waste_type: str) -> list[Collection]:
    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7
    first = today + timedelta(days=days_ahead)
    icon = ICON_MAP.get(waste_type)
    candidates = [first + timedelta(weeks=i) for i in range(BULK_WEEKS_AHEAD)]
    return [
        Collection(date=d, t=waste_type, icon=icon)
        for d in candidates
        if _week_color(d) == color
    ]


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(ADDRESS_URL, params={"address": self._address}, timeout=30)
        r.raise_for_status()
        suggestions_raw = r.json()

        target = _normalize(self._address)
        matches = [
            entry
            for entry in suggestions_raw
            if _normalize(entry.get("address", "")) == target
        ]

        if not matches:
            suggestions = sorted(
                {
                    entry["address"].strip()
                    for entry in suggestions_raw
                    if entry.get("address")
                }
            )
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "address", self._address, suggestions[:10]
                )
            raise SourceArgumentNotFound("address", self._address)

        entries: list[Collection] = []
        for match in matches:
            r = requests.get(
                SCHEDULE_URL,
                params={
                    "customernumber": match["customernumber"],
                    "serviceid": match["serviceid"],
                },
                timeout=30,
            )
            r.raise_for_status()
            for row in r.json():
                entries.extend(self._parse_row(row))

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        # De-duplicate in case multiple service ids at the same address share
        # the same pickup day.
        unique = {(c.date, c.type): c for c in entries}
        return sorted(unique.values(), key=lambda c: c.date)

    @staticmethod
    def _parse_row(row: dict) -> list[Collection]:
        collections: list[Collection] = []

        for day_name, weekday in WEEKDAYS.items():
            if row.get(f"pickup{day_name.lower()}") == "Yes":
                collections.extend(_weekly_dates(weekday, GARBAGE_RECYCLING))
                break

        bulk = (row.get("yw_bulk") or "").strip()
        if bulk:
            parts = bulk.split()
            if len(parts) == 2:
                color, day_name = parts
                weekday = WEEKDAYS.get(day_name)
                if weekday is not None and color in ("Red", "Blue"):
                    collections.extend(
                        _biweekly_dates(weekday, color, BULKY_YARD_WASTE)
                    )

        return collections
