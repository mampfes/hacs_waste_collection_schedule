import json
from datetime import date

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mosman Council"
DESCRIPTION = "Source for Mosman Council, NSW, Australia"
URL = "https://mosman.nsw.gov.au/"
TEST_CASES = {
    "Test_001": {"address": "12 Shadforth Street"},
    "Test_002": {"address": "19 Rangers Avenue"},
    "Test_003": {"address": "14 Balmoral Avenue"},
}

API_URL = "https://apps.mosman.nsw.gov.au/test"
ICON_MAP = {
    "generalWaste": "mdi:trash-can",
    "containersGlass": "mdi:recycle",
    "paperCardboard": "mdi:recycle",
    "vegetation": "mdi:leaf",
    "generalCleanUp": "mdi:trash-can",
    "ewaste": "mdi:battery-sync",
}

COLLECTIONS_MAP = {
    "generalWaste": "Rubbish",
    "containersGlass": "Plastic & Glass Recycling",
    "paperCardboard": "Paper Recycling",
    "vegetation": "Garden",
    "generalCleanUp": "Council Cleanup",
    "ewaste": "eWaste",
}

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,tr;q=0.8",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "sec-ch-ua": "Chromium;v=122, Not(A:Brand;v=24, Google Chrome;v=122",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "macOS",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "referrer": "https://mosman.nsw.gov.au/",
    "referrerPolicy": "strict-origin-when-cross-origin",
    "mode": "cors",
    "credentials": "omit",
}


class Source:
    def __init__(self, address):
        self._address = str(address)

    def fetch(self):
        params = {"address": self._address}
        r = requests.post(API_URL, headers=HEADERS, data=params)
        json_data = json.loads(r.text)
        entries = []

        for item in json_data:
            collection_date = date.fromisoformat(item["calendarDate"][:10])
            entries.append(
                Collection(
                    date=collection_date,
                    t=COLLECTIONS_MAP.get(item["type"], item["type"]),
                    icon=ICON_MAP.get(item["type"]),
                )
            )

        return entries
