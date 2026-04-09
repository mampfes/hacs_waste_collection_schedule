from datetime import date, datetime, timedelta

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Philadelphia, PA"
DESCRIPTION = "City of Philadelphia, PA, USA"
URL = "https://www.phila.gov/"
COUNTRY = "us"
TEST_CASES = {
    "Test_001": {"address": "1830 Fitzwater Street"},
    "Test_002": {"address": "9868 Cowden St"},
    "Test_003": {"address": "582 Paoli Ave"},
    "Test_004": {"address": "2714 S Marvine St"},
}
HEADERS = {"user-agent": "Mozilla/5.0"}
DAYS = {
    "MON": MO,
    "TUE": TU,
    "WED": WE,
    "THU": TH,
    "FRI": FR,
    "SAT": SA,
    "SUN": SU,
}
ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycle": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Search for your collection schedule at [phila.gov](https://www.phila.gov/services/trash-recycling-city-upkeep/find-your-trash-and-recycling-collection-day), use your address as it is displayed on the search results.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street name and house number of the property",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street name and house number of the property",
    },
}


class Source:
    def __init__(self, address: str):
        self._address: str = address.upper()

    def create_dates(self, days: list, start: date, end: date):
        all_pickups = []

        for index, day in enumerate(days):
            occurrences = rrule(freq=WEEKLY, byweekday=day, dtstart=start, until=end)

            for dt in occurrences:
                all_pickups.append({"date": dt.date(), "weekly_pickup_num": index + 1})
        return sorted(all_pickups, key=lambda x: x["date"])

    def check_holidays(self, hols: list[date], dt: date, pickup_number: int) -> date:
        """
        Shift a collection date forward for holidays in the same week.

        Rules per phila.gov:
        - Weekend holidays: already excluded from hols, no effect.
        - One holiday in the week: all collections on or after that holiday
          are shifted by 1 day.
        - Two holidays in the same week: collections shift by 1 or 2 days
          depending on how many holidays fall on or before the collection day.
        - If the shifted date itself lands on a holiday, shift again.
        """
        # find all weekday holidays in the same Mon-Sun week as dt
        week_start = dt - timedelta(days=dt.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday
        week_hols = sorted(h for h in hols if week_start <= h <= week_end)

        # shift by 1 for each holiday that falls on or before the collection day
        shift = sum(1 for h in week_hols if h <= dt)
        adjusted = dt + timedelta(days=shift)

        # if the adjusted date itself is a holiday, shift once more
        if adjusted in hols and adjusted != dt:
            adjusted = self.check_holidays(hols, adjusted, pickup_number)

        return adjusted

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        # get list of observed holidays
        # weekend holidays are excluded as they don't affect collections
        holidays = []
        h_json = s.get(
            "https://api.phila.gov/phila/trashday/v1",
            headers=HEADERS,
        ).json()
        for item in h_json["holidays"]:
            h_date = datetime.strptime(item["start_date"], "%Y-%m-%d").date()
            if h_date.weekday() not in [5, 6]:
                holidays.append(h_date)

        # get property info
        p_json = s.get(
            f"https://api.phila.gov/ais/v1/addresses/{self._address}",
            headers=HEADERS,
        ).json()

        props = p_json["features"][0]["properties"]

        # extract collection days
        # rubbish_recycle_day   = primary day for BOTH trash and recycling
        # secondary_rubbish_day = second trash-only day (some addresses)
        waste_days = []
        recycle_days = []

        for key in props:
            val = props[key]
            if not isinstance(val, str) or val.upper() not in DAYS:
                continue
            day = DAYS[val.upper()]
            if "rubbish" in key.lower():
                # rubbish_recycle_day and secondary_rubbish_day both go into trash
                waste_days.append(day)
            if key.lower() == "rubbish_recycle_day":
                # the primary day is also the recycling day
                recycle_days.append(day)

        # generate day dates for the current year
        year = datetime.now().year
        start: date = date(year, 1, 1)
        end: date = date(year, 12, 31)
        trash = self.create_dates(waste_days, start, end)
        recycle = self.create_dates(recycle_days, start, end)

        # adjust for observed holidays
        adjusted_trash = [
            self.check_holidays(holidays, item["date"], item["weekly_pickup_num"])
            for item in trash
        ]
        adjusted_recycling = [
            self.check_holidays(holidays, item["date"], item["weekly_pickup_num"])
            for item in recycle
        ]
        waste_schedule = list({d for d in adjusted_trash if d is not None})
        recycle_schedule = list({d for d in adjusted_recycling if d is not None})

        entries = []
        for item in waste_schedule:
            entries.append(
                Collection(date=item, t="Rubbish", icon=ICON_MAP.get("Rubbish"))
            )
        for item in recycle_schedule:
            entries.append(
                Collection(date=item, t="Recycle", icon=ICON_MAP.get("Recycle"))
            )

        return entries
