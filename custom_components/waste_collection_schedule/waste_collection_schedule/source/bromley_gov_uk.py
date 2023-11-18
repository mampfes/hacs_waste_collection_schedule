import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "London Borough of Bromley"
DESCRIPTION = "Source for bromley.gov.uk services for London Borough of Bromley, UK."
URL = "https://bromley.gov.uk"
TEST_CASES = {
    "Test_001": {"property": 6328436},
    "Test_002": {"property": "6146611"},
    "Test_003": {"property": 6283460},
}

ICON_MAP = {
    "NON-RECYCLABLE": "mdi:trash-can",
    "FOOD": "mdi:food",
    "GARDEN": "mdi:leaf",
    "PAPER": "mdi:newspaper",
    "MIXED": "mdi:glass-fragile",
}

MAX_COUNT = 15


class Source:
    def __init__(self, property):
        self._property = str(property)
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        r = s.get(f"https://recyclingservices.bromley.gov.uk/waste/{self._property}")

        for _ in range(MAX_COUNT):
            r = s.get(
                f"https://recyclingservices.bromley.gov.uk/waste/{self._property}/calendar.ics"
            )
            try:
                dates = self._ics.convert(r.text)
                break
            except ValueError:
                time.sleep(2)  # identical to website behaviour (hx-trigger="every 2s")

        entries = []
        for item in dates:
            bin_type = item[1].replace(" collection", "")
            entries.append(
                Collection(
                    date=item[0],
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type.split(" ")[0].upper()),
                )
            )

        return entries
