from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wollondilly Shire Council"
DESCRIPTION = "Source for Wollondilly Shire Council."
URL = "https://www.wollondilly.nsw.gov.au/"
TEST_CASES = {
    "87 Remembrance Driveway TAHMOOR NSW": {
        "address": "87 Remembrance Driveway TAHMOOR NSW"
    },
    "Thirlmere Way THIRLMERE NSW": {"address": "Thirlmere Way THIRLMERE NSW"},
}


ICON_MAP = {
    "garbage": "mdi:trash-can",
    "garden organic": "mdi:leaf",
    "recycling": "mdi:recycle",
}


ADDRESS_URL = "https://yokqi4ofx1.execute-api.ap-southeast-2.amazonaws.com/Live/wcc_address_lookup"
INFO_URL = "https://yokqi4ofx1.execute-api.ap-southeast-2.amazonaws.com/Live/wcc_details_lookup"


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self):
        args = {"fields": self._address}

        r = requests.get(ADDRESS_URL, params=args)
        r.raise_for_status()

        data = r.json()
        if len(data) == 0:
            raise Exception("Address not found")

        id = data[0][1]["value"]
        args = {"fields": id}
        r = requests.get(INFO_URL, params=args)
        r.raise_for_status()

        data = r.json()
        entries = []
        for collection in data[0]:
            if "WasteNextPickup" not in collection["name"]:
                continue
            info_arr = collection["value"].split(", ")
            date_str = info_arr[1]
            collection_str = info_arr[2]
            date = datetime.strptime(date_str, "%d %B %Y").date()
            collection_types = collection_str.split(" and ")
            for col_type in collection_types:
                icon = ICON_MAP.get(col_type.lower())
                entries.append(Collection(date=date, t=col_type, icon=icon))
        return entries
