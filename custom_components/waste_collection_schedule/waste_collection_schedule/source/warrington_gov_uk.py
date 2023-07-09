import requests
import json

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Warrington Borough Council"
DESCRIPTION = "Source for warrington.gov.uk services for Warrington Borough Council, UK."
URL = "https://www.warrington.gov.uk"

TEST_CASES = {
    "Test_001": {"uprn": "100010309878"},
    "Test_002": {"uprn": "100010296572"},
    "Test_003": {"uprn": 100010291332},
    "Test_004": {"uprn": 100010258176},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "BLACK BIN": "mdi:trash-can",
    "BLUE BIN": "mdi:recycle",
    "GREEN BIN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):

        s = requests.Session()
        r = s.get(f"https://www.warrington.gov.uk/bin-collections/get-jobs/{self._uprn}", headers=HEADERS)
        json_data = json.loads(r.text)

        entries = []

        # If no schedule, return empty list.
        if not json_data["schedule"]:
            return entries

        for job in json_data["schedule"]:
            # Data doesn't contain bin type, so we need to extract it from the job name.
            bin_type = self.get_type(job["Name"])
            if not bin_type:
                continue

            # List contains duplicates, so skip if already added.
            if self.contains(entries, lambda x: x.date == datetime.strptime(job["ScheduledStart"], "%Y-%m-%dT%H:00:00").date() and x.type == bin_type):
                continue

            entries.append(
                Collection(
                    date=datetime.strptime(job["ScheduledStart"], "%Y-%m-%dT%H:00:00").date(),
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type.upper())
                )
            )

        return entries

    def get_type(self, name):
        if "BLACK" in name:
            return "Black Bin"
        if "BLUE" in name:
            return "Blue Bin"
        if "GREEN" in name:
            return "Green Bin"
        return False

    def contains(self, list, filter):
        for x in list:
            if filter(x):
                return True
        return False
