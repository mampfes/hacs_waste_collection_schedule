from datetime import datetime, timedelta

import requests
import json

from dateutil.rrule import rrule, YEARLY, WEEKLY, MO, TU, WE, TH, FR, SA, SU

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Round Rock Texas"
DESCRIPTION = "Source for bin collection services for Round Rock, Texas"
URL = "https://www.roundrocktexas.gov/"
TEST_CASES = {
    "Apache Oaks": {"neighborhood": "Apache Oaks"},
    "Mayfield Ranch": {"neighborhood": "Mayfield Ranch"},
    "Windy Park": {"neighborhood": "Windy Park"},
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Trash": "mdi:trash-can",
}
DAYS = {
    "Monday": MO,
    "Tuesday": TU,
    "Wednesday": WE,
    "Thursday": TH,
    "Friday": FR,
    "Saturday": SA,
    "Sunday": SU,
}
HOLIDAYS = { # website indicates collections falling on these days will be shifted by 1 day
    "Thanksgiving": list(rrule(YEARLY, bymonth=11, byweekday=TH(4), dtstart=datetime.now()))[0].date(), # 4th Thursday in November
    "Christmas Day": list(rrule(YEARLY, bymonth=12, bymonthday=25, dtstart=datetime.now()))[0].date(), # 25th December
    "New Years Day": list(rrule(YEARLY, bymonth=1, bymonthday=1, dtstart=datetime.now()))[0].date(), # 1st January
}


class Source:
    def __init__(self, neighborhood: str):
        self._area = neighborhood

    def check_holidays(self, dt):
        for _, holiday in enumerate(HOLIDAYS):
            if dt == HOLIDAYS[holiday]:
                dt += timedelta(days=1)
        return dt

    def fetch(self):
        today = datetime.now()
        s = requests.Session()

        # get recycling zone - determines which day of the week collections are made
        r = s.get("https://devcorrpublicdatahub.blob.core.usgovcloudapi.net/garbage-recycling/garbagerecyclingzones.json")
        r.raise_for_status()
        areas = json.loads(r.text)
        for idx, area in enumerate(areas):
            if self._area.upper() == area["Neighborhood Name"].upper():
                recycling_zone = area["Recycling Zone"]

        entries = []

        # get recycling schedules - collections are every 2 weeks
        r = s.get("https://devcorrpublicdatahub.blob.core.usgovcloudapi.net/garbage-recycling/garbagerecyclingdays.json")
        r.raise_for_status()
        recycling_schedule = json.loads(r.text)
        for idx, zone in enumerate(recycling_schedule):
            if recycling_zone == zone["Recycling Zone"]:
                end_date = datetime.strptime(zone["Date"], "%Y-%m-%d")
                dt = datetime.strptime(zone["Date"], "%Y-%m-%d").date()
                dt = self.check_holidays(dt)
                entries.append(
                    Collection(
                        date=datetime.strptime(zone["Date"], "%Y-%m-%d").date(),
                        t="Recycling",
                        icon=ICON_MAP.get("Recycling"),
                    )
                )

        # generate weekly trash schedule - occur weekly, the same week day as recycling collections
        trash_day = recycling_zone.split(" ")[0]
        trash_dates = list(rrule(WEEKLY, byweekday=DAYS[trash_day], dtstart=today, until=end_date))
        for idx, item in enumerate(trash_dates):
            item = self.check_holidays(item.date())
            entries.append(
                Collection(
                    date=item,
                    t="Trash",
                    icon=ICON_MAP.get("Trash"),
                )
            )

        return entries
