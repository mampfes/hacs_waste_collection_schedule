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


class Source:
    def __init__(self, address: str):
        self._address: str = address.upper()

    def create_dates(self, days: list, start: date, end: date):
        dts = list(rrule(freq=WEEKLY, byweekday=days, dtstart=start, until=end))
        return dts

    def check_holidays(self, hols: list[date], dt: date) -> date:
        # collections shifted by 1 day if they fall on a holiday
        # if adjusted day is also a holiday, it shifts again
        if dt in hols:
            x = dt + timedelta(days=1)
            x = self.check_holidays(hols, x)
        else:
            x = dt
        return x

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        # get list of observed holidays
        holidays = []
        h_json = s.get(
            "https://api.phila.gov/phila/trashday/v1",
            headers=HEADERS,
        ).json()
        for item in h_json["holidays"]:
            h_date = datetime.strptime(item["start_date"], "%Y-%m-%d").date()
            # weekend holidays don't impact collections so remove them
            if h_date.weekday() not in [5, 6]:
                holidays.append(h_date)

        # get property info
        p_json = s.get(
            f"https://api.phila.gov/ais/v1/addresses/{(self._address)}", headers=HEADERS
        ).json()
        # extract collection days
        waste_days = []
        recycle_days = []
        for item in p_json["features"][0]["properties"]:
            if "rubbish_" in item:
                try:
                    waste_days.append(DAYS[p_json["features"][0]["properties"][item]])
                except KeyError:  # not all keys have values
                    pass
            if "recycle_" in item:
                try:
                    recycle_days.append(DAYS[p_json["features"][0]["properties"][item]])
                except KeyError:  # not all keys have values
                    pass
        # generate day dates
        year = datetime.now().year
        start: date = date(year, 1, 1)
        end: date = date(year, 12, 31)
        trash = self.create_dates(waste_days, start, end)
        recycle = self.create_dates(recycle_days, start, end)
        # adjust for observed holidays
        adjusted_trash = []
        adjusted_recycling = []
        for item in trash:
            adjusted_trash.append(self.check_holidays(holidays, item.date()))
        for item in recycle:
            adjusted_recycling.append(self.check_holidays(holidays, item.date()))
        waste_schedule = list(set(adjusted_trash))
        recycle_schedule = list(set(adjusted_recycling))

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
