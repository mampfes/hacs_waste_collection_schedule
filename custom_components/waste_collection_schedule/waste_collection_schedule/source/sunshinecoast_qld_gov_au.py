from datetime import datetime, timedelta

import requests
from dateutil import rrule
from waste_collection_schedule import Collection

TITLE = "Sunshine Coast Queensland (QLD)"
DESCRIPTION = "Source script for Sunshine Coast Queensland (QLD)."
COUNTRY = "au"
URL = "https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days"
TEST_CASES = {
    "Hospital Rd": {"street_name": "hospital rd"},
    "Great Keppel Way": {"street_name": "great keppel way"},
}

API_URL = "https://www.sunshinecoast.qld.gov.au/__server__/api/v1"
ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycle": "mdi:recycle",
    "Organic": "mdi:leaf",
}

"""
    WEEK TYPES
        sunshine coast uses a week setting
        week 1 and week 2 starting from a set date


    RETURNED VALUES FROM API Query
        JSON DATA:
            [{"id":"<id>","street":"<Street Name>","locality":"<Town>","day":"Wednesday","week":"1","instructions":""}]
"""


class Source:
    def __init__(
        self, street_name
    ):  # argX correspond to the args dict in the source configuration
        self.street_name = street_name

    def fetch(self):
        r = requests.get(f"{API_URL}/streets/{self.street_name}")

        if len(r.json()) == 0:
            return []

        data = r.json()[0]

        day = datetime(2021, 12, 11)
        for _ in range(7):
            if day.strftime("%A") == data["day"]:
                break
            day += timedelta(days=1)

        day += timedelta(weeks=int(data["week"]) - 1)

        today = datetime.today()

        general_dates = rrule.rrule(rrule.WEEKLY, dtstart=day).xafter(today, 10, True)
        recycling_dates = rrule.rrule(rrule.WEEKLY, interval=2, dtstart=day).xafter(
            today, 10, True
        )
        garden_dates = rrule.rrule(
            rrule.WEEKLY, interval=2, dtstart=day + timedelta(weeks=1)
        ).xafter(today, 10, True)

        entries = []
        for text, dates in [
            ("Garbage", general_dates),
            ("Recycle", recycling_dates),
            ("Organic", garden_dates),
        ]:
            for date in dates:
                entries.append(
                    Collection(
                        date=date.date(),
                        t=text,
                        icon=ICON_MAP[text],
                    )
                )

        return entries
