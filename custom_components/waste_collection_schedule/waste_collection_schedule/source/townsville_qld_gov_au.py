from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Townsville"
DESCRIPTION = "Source for Townsville."
URL = "https://townsville.qld.gov.au/"
TEST_CASES = {
    "Woodwark Drive, Bushland Beach": {
        "property_id": "009fe2d01b9ba090598520202d4bcbc7"
    },
    "Riverway Dr, Kelso": {"property_id": "d41fe69c1b5ba090598520202d4bcb3c"},
    "37 Pilkington St, Garbutt": {"property_id": "580f6e5c1b5ba090598520202d4bcb91"},
}


ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycle": "mdi:recycle",
}


API_URL = "https://mitownsville.service-now.com/api/cio19/bin_collection_dates/getBinCollectionCal"


class Source:
    def __init__(self, property_id: str):
        self._property_id: str = property_id

    def fetch(self) -> list[Collection]:
        params = {"p_id": self._property_id}

        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()

        entries = []
        for d in data["result"]:
            bin_type = d["title"]
            # date format like: 2024-01-03T00:00:00+00:00
            date = datetime.strptime(d["start"], "%Y-%m-%dT%H:%M:%S%z").date()
            icon = ICON_MAP.get(bin_type)  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
