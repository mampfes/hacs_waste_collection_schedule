from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]


TITLE = "East Northamptonshire and Wellingborough"
DESCRIPTION = "Source for East Northamptonshire and Wellingborough"
URL = "east-northamptonshire.gov.uk"
TEST_CASES = {
    "Raunds": {"uprn": "100031046896"},
    "Rusheden": {"uprn": "100031028202"},
    "Easton on the Hill": {"uprn": 100031040850},
    "Lutton": {"uprn": 200000735573},
    "Wellingborough": {"uprn": 100031193921},
}

ICON_MAP = {
    "general": "mdi:trash-can",
    "recycling": "mdi:recycle",
}


API_URL = "https://api.northnorthants.gov.uk/test/wc-info/{uprn}"

DAYS = {
    'MON': 0,
    'TUE': 1,
    'WED': 2,
    'THU': 3,
    'FRI': 4
}


class Source:
    def __init__(self, uprn: str):
        self._uprn: str = uprn
        print(self._uprn)

    def fetch(self):
        r = requests.get(API_URL.format(uprn=self._uprn))
        r.raise_for_status()
        r.json()

        data = r.json()

        process_day = datetime.now()
        while process_day.weekday() != DAYS.get(data["day"]):
            process_day = process_day + timedelta(days=1)

        reference_date = datetime(2022, 6, 20)
        entries = []

        for _ in range(10):
            weeks_diff: int = int((process_day - reference_date).days / 7)
            if weeks_diff % 2 == 0:
                bin_type = "general" if data["schedule"] == "B" else "recycling"
            else:
                bin_type = "recycling" if data["schedule"] == "B" else "general"

            entries.append(Collection(date=process_day.date(),
                           t=bin_type, icon=ICON_MAP.get(bin_type)))

            process_day = process_day + timedelta(days=7)

        return entries
