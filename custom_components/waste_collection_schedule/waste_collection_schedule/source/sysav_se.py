import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Sysav Sophämntning"
DESCRIPTION = "Source for Sysav waste collection."
URL = "https://www.sysav.se"
TEST_CASES = {
    "Home": {"street_address": "Sommargatan 1, Svedala"},
    "Polisen": {"street_address": "Stationsplan 1, Svedala"},
    "Svedala": {"street_address": "Ekhagsvägen 204, Svedala"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        params = {"address": self._street_address}
        response = requests.get(
            "https://www.sysav.se/api/my-pages/PickupSchedule/findAddress",
            params=params,
        )

        address_data = json.loads(response.text)
        address = None
        if address_data and len(address_data) > 0:
            address = address_data[0]

        if not address:
            return []

        params = {"address": address}
        response = requests.get(
            "https://www.sysav.se/api/my-pages/PickupSchedule/ScheduleForAddress",
            params=params,
        )

        data = json.loads(response.text)

        entries = []
        for item in data:
            waste_type = item["WasteType"]
            icon = "mdi:trash-can"
            if waste_type == "Trädgårdsavfall":
                icon = "mdi:leaf"
            next_pickup = item["NextPickupDate"]

            res = re.match(r"v(\d*)\s+\w+\s*(\d+)", next_pickup)
            if res:
                next_pickup_date = datetime.fromisocalendar(
                    year=int(res.group(2)), week=int(res.group(1)), day=1
                ).date()
            else:
                next_pickup_date = datetime.fromisoformat(next_pickup).date()

            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
