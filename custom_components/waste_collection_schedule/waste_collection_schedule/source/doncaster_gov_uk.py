import json
import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Doncaster Council"
DESCRIPTION = (
    "Source for doncaster.gov.uk services for the City of Doncaster Council, UK."
)
URL = "https://doncaster.gov.uk"

TEST_CASES = {
    "Test_001": {"uprn": "100050701118"},
    "Test_002": {"uprn": "100050753396"},
    "Test_003": {"uprn": 100050699118},
}

ICON_MAP = {
    "GREEN": "mdi:leaf",
    "RECYCLING": "mdi:recycle",
    "BLACK": "mdi:trash-can",
    "BULKY": "mdi:fridge",
    "RE-USE": "mdi:sofa",
}

REGEX_DATE = r"\(([0-9]{10})"


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        # Query needs start and end epoch dates
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = (today - timedelta(days=365)).strftime("%s")
        end = (today + timedelta(days=365)).strftime("%s")
        url = f"https://www.doncaster.gov.uk/Compass/PremiseDetail/GetCollectionsForCalendar?UPRN={self._uprn}&Start={start}&End={end}"
        # start = start.strftime("%s")
        # end = end.strftime("%s")

        s = requests.Session()
        r = s.get(url)
        data = json.loads(r.text)

        entries = []

        for entry in data["slots"]:
            waste_type = entry["title"]
            waste_date = entry["end"]
            epoch = re.findall(REGEX_DATE, waste_date)
            waste_date = datetime.fromtimestamp(int(epoch[0])).date()
            entries.append(
                Collection(
                    date=waste_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.upper()),
                )
            )

        return entries
