import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of York Council"
DESCRIPTION = "Source for York.gov.uk services for the city of York, UK."
URL = "https://york.gov.uk"
TEST_CASES = {
    "Reighton Avenue, York": {"uprn": "100050580641"},
    "Granary Walk, York": {"uprn": "010093236548"},
}

ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        # get json file
        r = requests.get(
            f"https://waste-api.york.gov.uk/api/Collections/GetBinCalendarDataForUprn/{self._uprn}"
        )

        # extract data from json
        data = json.loads(r.text)

        entries = []

        for collection in data["collections"]:
            try:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            collection["date"], "%Y-%m-%dT%H:%M:%S"
                        ).date(),
                        t=collection["roundType"].title(),
                        icon=ICON_MAP.get(collection["roundType"]),
                    )
                )
            except ValueError:
                pass  # ignore date conversion failure for not scheduled collections

        return entries
