import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Armadale (Western Australia)"
DESCRIPTION = "Source for Armadale (Western Australia)."
URL = "https://my.armadale.wa.gov.au"
TEST_CASES = {
    "23 Sexty St, ARMADALE": {"address": "23 Sexty St, ARMADALE"},
    "270 Skeet Rd, HARRISDALE": {"address": "270 Skeet Rd, HARRISDALE"},
}

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

API_URL = "https://api.my.armadale.wa.gov.au/bins"


def easter(year):
    # taken from dateutil easter https://dateutil.readthedocs.io/en/stable/_modules/dateutil/easter.html to prevent dependency

    y = year
    g = y % 19
    e = 0

    # New method
    c = y // 100
    h = (c - c // 4 - (8 * c + 13) // 25 + 19 * g + 15) % 30
    i = h - (h // 28) * (1 - (h // 28) * (29 // (h + 1)) * ((21 - g) // 11))
    j = (y + y // 4 + i + 2 - c + c // 4) % 7

    # p can be from -6 to 56 corresponding to dates 22 March to 23 May
    # (later dates apply to method 2, although 23 May never actually occurs)
    p = i - j + e
    d = 1 + (p + 27 + (p + 6) // 40) % 31
    m = 3 + (p + 26) // 30
    return datetime.date(int(y), int(m), int(d))


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self):
        r = requests.get(API_URL, params={"address": self._address})
        r.raise_for_status()

        data = r.json()
        if not data:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        result = data[0]
        bin_day = result["bin_day"]
        if bin_day not in WEEKDAYS:
            raise Exception(f"Unknown bin day: {bin_day}")
        bin_day = WEEKDAYS[bin_day]

        recycling: bool = result["recycle_area"].lower().startswith("this week")

        current_day = datetime.datetime.now().date()

        diff_to_next = (bin_day - current_day.weekday()) % 7

        # next is next week
        if current_day.weekday() + diff_to_next >= 7:
            recycling = not recycling

        current_day = current_day + datetime.timedelta(days=diff_to_next)

        entries = []
        for i in range(52):
            date = current_day
            start_of_week = date - datetime.timedelta(days=date.weekday())

            christmas = datetime.date(current_day.year, 12, 25)
            new_years_day = datetime.date(
                current_day.year + (1 if current_day.month == 12 else 0), 1, 1
            )
            good_friday = easter(current_day.year) - datetime.timedelta(days=2)

            if (
                start_of_week <= christmas <= date
                or start_of_week <= new_years_day <= date
            ):
                # if christmas or new years day is in the current week
                if 0 <= christmas.weekday() < 5:  # if christmas is on a weekday
                    date += datetime.timedelta(days=1)

            if date == good_friday:
                date += datetime.timedelta(days=1)

            entries.append(Collection(date=date, t="rubbish", icon="mdi:trash-can"))
            if recycling:
                entries.append(Collection(date=date, t="recycling", icon="mdi:recycle"))

            current_day += datetime.timedelta(days=7)
            recycling = not recycling

        return entries
