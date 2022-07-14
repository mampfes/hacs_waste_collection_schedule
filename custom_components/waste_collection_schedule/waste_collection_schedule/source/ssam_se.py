import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "SSAM Sophämntning"
DESCRIPTION = "Source for SSAM waste collection."
URL = "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule"
TEST_CASES = {
    "Home": {"street_address": "Saturnusvägen 12, Växjö"},
    "Other": {"street_address": "Andvägen 3, Växjö"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        params = {"searchText": self._street_address}
        print(self._street_address)
        response = requests.post(
            "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/SearchAdress",
            params=params,
        )

        address_data = json.loads(response.text)
#        print(json.dumps(address_data, indent=4, sort_keys=True))
        address = None

        if address_data and len(address_data) > 0:
            address = address_data["Buildings"][0]

        if not address:
            return []

        params = {"address": address}
        response = requests.get(
            "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule",
            params=params,
        )

        data = json.loads(response.text)
#        print(json.dumps(data, indent=4, sort_keys=True))

        entries = []
        for item in data["RhServices"]:
#            print(json.dumps(item, indent=4, sort_keys=True))
            if item["WasteType"] == "FNI1":
                waste_type = "Kärl 1"
                icon = "mdi:trash-can"
            elif item["WasteType"] == "FNI2":
                waste_type = "Kärl 2"
                icon = "mdi:trash-can"
            if waste_type == "Trädgårdsavfall":
                icon = "mdi:leaf"
            next_pickup = item["NextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
