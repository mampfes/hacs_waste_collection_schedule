import re
from datetime import date

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Darlington Borough Council"
DESCRIPTION = "Source for Darlington Borough Council."
URL = "https://darlington.gov.uk"
TEST_CASES = {
    "010013315817": {"uprn": 10013315817},
    "100110560916": {"uprn": 100110560916},
    "200002724471": {"uprn": "200002724471"},
}


ICON_MAP = {
    "Recycle": "mdi:recycle",
    "Refuse": "mdi:trash-can",
    "Garden": "mdi:leaf",
}


API_URL = "https://www.darlington.gov.uk/bins-waste-and-recycling/calendar/"

WASTE_TYPES = ["Recycle", "Refuse", "Garden"]

DATE_REGEX = re.compile(r"calDates.push\(new Date\((\d+)\)\);")


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn).zfill(12)

    def fetch(self) -> list[Collection]:
        args = {"uprn": self._uprn}

        entries = []
        for waste_type in WASTE_TYPES:
            args["collectiontype"] = waste_type
            icon = ICON_MAP.get(waste_type)

            r = requests.get(API_URL, params=args)
            r.raise_for_status()

            # find all unix timestamps in the response
            dates_list = re.findall(DATE_REGEX, r.text)

            for date_str in dates_list:
                d = date.fromtimestamp(int(date_str) / 1000)
                entries.append(Collection(date=d, t=waste_type, icon=icon))

        return entries
