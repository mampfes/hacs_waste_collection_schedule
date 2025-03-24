import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "London Borough of Bexley"
DESCRIPTION = "Source for bexley.gov.uk services for London Borough of Bexley, UK."
URL = "https://bexley.gov.uk"
TEST_CASES = {
    "Test_001": {"property": 100020217315},
    "Test_002": {"property": "100020215608"},
    "Test_003": {"property": 100020254340},
}

ICON_MAP = {
    "Green Wheelie Bin": "mdi:trash-can",
    "Brown Caddy": "mdi:food",
    "Brown Wheelie Bin": "mdi:leaf",
    "Blue Lidded Wheelie Bin": "mdi:newspaper",
    "White Lidded Wheelie Bin": "mdi:glass-fragile",
}

MAX_COUNT = 15


class Source:
    def __init__(self, property):
        self._property = str(property)
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        r = s.get(f"https://waste.bexley.gov.uk/waste/{self._property}")

        for _ in range(MAX_COUNT):
            r = s.get(
                f"https://waste.bexley.gov.uk/waste/{self._property}/calendar.ics"
            )
            try:
                dates = self._ics.convert(r.text)
                break
            except ValueError:
                time.sleep(2)  # identical to website behaviour (hx-trigger="every 2s")

        entries = []
        for item in dates:
            bin_type = item[1].replace(" Bin", "")
            entries.append(
                Collection(
                    date=item[0],
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type.split("(")[0]),
                )
            )

        return entries
