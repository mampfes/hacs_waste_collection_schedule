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
    "Furulund": {"street_address": "Asagatan 2, Furulund"},
    "Käglinge": {"street_address": "Kvarngatan 13, Kävlinge"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        r = requests.get("https://www.sysav.se/privat/min-sophamtning/")
        data_api = re.search(r"data-api\s*=\s*\"([^\"]+)\"", r.text).group(1)
        response = requests.get(
            f"{data_api}/PickupSchedules/findbuilding/{self._street_address}"
        )

        address_data = json.loads(response.text)
        address = None
        if address_data and len(address_data) > 0:
            address = address_data[0]

        if not address:
            return []

        response = requests.get(f"{data_api}/PickupSchedules/foraddress/{address}")
        data = json.loads(response.text)

        entries = []
        for item in data:
            waste_type = item["wasteType"]
            icon = None
            if waste_type == "Trädgårdsavfall":
                icon = "mdi:leaf"
            next_pickup = item["nextPickupDate"]

            res = re.match(r"v(\d*)\s+\w+\s*(\d+)", next_pickup)
            if res:
                next_pickup_date = datetime.fromisocalendar(
                    year=int(res.group(2)), week=int(res.group(1)), day=1
                ).date()
            else:
                next_pickup_date = datetime.fromisoformat(next_pickup).date()

            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
