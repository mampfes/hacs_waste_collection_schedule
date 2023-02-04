from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection

TITLE = "Wollongong City Council"
DESCRIPTION = "Source script for wollongongwaste.com.au"
URL = "https://wollongongwaste.com"
COUNTRY = "au"
TEST_CASES = {"TestName1": {"propertyID": "21444"}}

API_URL = "https://wollongong.waste-info.com.au/api/v1/properties/"

ICON_MAP = {
    "waste": "mdi:trash-can",
    "organic": "mdi:leaf",
    "recycle": "mdi:recycle",
}


def day_of_week(start_date, end_date, day_of_week_index):
    day_of_week_dates = []
    while start_date <= end_date:
        if start_date.weekday() == day_of_week_index:
            day_of_week_dates.append(start_date)
        start_date += timedelta(days=1)
    return day_of_week_dates


class Source:
    def __init__(self, propertyID):
        self._propertyID = propertyID

    def fetch(self):
        # Have to specify a start and end, or the API returns nothing. So lets request this year, and next year.
        # start=2022-12-31T13:00:00.000Z&end=2024-12-30T13:00:00.000Z
        startdate = datetime(date.today().year - 1, 12, 31, 13, 0, 0)
        enddate = datetime(date.today().year + 1, 12, 31, 13, 0, 0)

        data = {
            "start": startdate.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "end": enddate.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        r = requests.get(f"{API_URL}{self._propertyID}.json", data=data)
        r.raise_for_status()
        d = r.json()

        entries = []
        for entry in d:
            waste_type = entry["event_type"]
            if waste_type in ("waste", "organic"):
                for day in entry["daysOfWeek"]:
                    for pickupdate in day_of_week(startdate, enddate, day - 1):
                        entries.append(
                            Collection(
                                date=pickupdate.date(),
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )
            if waste_type in ("recycle"):
                entries.append(
                    Collection(
                        date=date(*map(int, entry["start"].split("-"))),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )
        return entries
