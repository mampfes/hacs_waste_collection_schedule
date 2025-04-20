import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "London Borough of Bexley"
DESCRIPTION = "Source for bexley.gov.uk services for London Borough of Bexley, UK."
URL = "https://bexley.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "200001604426"},
    "Test_002": {"uprn": 100020194783},
    "Test_003": {"uprn": "100020195768"},
    "Test_004": {"uprn": 100020200324},
}

ICON_MAP = {
    "Green Wheelie": "mdi:trash-can",
    "Brown Caddy": "mdi:food",
    "Brown Wheelie": "mdi:leaf",
    "Blue Lidded Wheelie": "mdi:newspaper",
    "White Lidded Wheelie": "mdi:glass-fragile",
    "Recycling Box": "mdi:recycle",
}

MAX_COUNT = 15


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        r = s.get(f"https://waste.bexley.gov.uk/waste/{self._uprn}")

        for _ in range(MAX_COUNT):
            r = s.get(f"https://waste.bexley.gov.uk/waste/{self._uprn}/calendar.ics")
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
                    icon=next(
                        (
                            icon
                            for bin, icon in ICON_MAP.items()
                            if bin.lower() in bin_type.lower().split("(")[0].strip()
                        ),
                        None,
                    ),
                )
            )

        return entries
