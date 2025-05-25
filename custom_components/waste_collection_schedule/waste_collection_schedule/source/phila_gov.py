from datetime import date, datetime, timedelta

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Philadelphia, PA"
DESCRIPTION = "City of Philadelphia, PA, USA"
URL = "https://www.phila.gov/"
COUNTRY = "us"
TEST_CASES = {
    "Test_001": "1830 Fitzwater Street",
    "Test_002": "9868 Cowden St",
    "Test_003": "582 Paoli Ave",
    "Test_004": "2714 S Marvine St",
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
        self._address: str = address
        self._holidays: list[date] = []
        self._waste_schedule: list[date] = []
        self._recycle_schedule: list[date] = []

    def create_dates(self, days: list, start: date, end: date):
        dts = list(rrule(freq=WEEKLY, byweekday=days, dtstart=start, until=end))
        return dts

    def check_holidays(self, hols: list[date], dt: date) -> date:
        # collections shifted by 1 day if they fall on a holiday
        # if adjusted day is also holiday, it shifts again
        if dt in hols:
            x = dt + timedelta(days=1)
            x = self.check_holidays(hols, x)
        else:
            x = dt
        return x

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        # get list of observed holidays
        h_json: dict = s.get(
            "https://api.phila.gov/phila/trashday/v1",
            headers=HEADERS,
        ).json()
        for item in h_json["holidays"]:
            h_date = datetime.strptime(item["start_date"], "%Y-%m-%d").date()
            # Weekend holidays don't impact collections so remove them
            if h_date.weekday() not in [5, 6]:
                self._holidays.append(h_date)

        # get property info
        p_json: dict = s.get(
            f"https://api.phila.gov/ais/v1/addresses/{(self._address)}", headers=HEADERS
        ).json()
        # extract collection days
        waste_days: list = []
        recycle_days: list = []
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
        trash: list[date] = self.create_dates(waste_days, start, end)
        recycle: list[date] = self.create_dates(recycle_days, start, end)
        # adjust for observed holidays
        adjusted_trash: list[date] = []
        adjusted_recycling: list[date] = []
        for item in trash:
            adjusted_trash.append(self.check_holidays(self._holidays, item.date()))
        for item in recycle:
            adjusted_recycling.append(self.check_holidays(self._holidays, item.date()))
        self._waste_schedule = list(set(adjusted_trash))
        self._recycle_schedule = list(set(adjusted_recycling))

        entries = []
        for item in self._waste_schedule:
            entries.append(
                Collection(date=item, t="Rubbish", icon=ICON_MAP.get("Rubbish"))
            )
        for item in self._recycle_schedule:
            entries.append(
                Collection(date=item, t="Recycle", icon=ICON_MAP.get("Recycle"))
            )

        return entries
