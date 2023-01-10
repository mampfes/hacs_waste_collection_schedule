import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "SSAM"
DESCRIPTION = "Source for SSAM waste collection."
URL = "https://ssam.se"
TEST_CASES = {
    "Home": {"street_address": "Asteroidvägen 1, Växjö"},
    "Bostadsrätt": {"street_address": "Långa Gatan 29 -81, Växjö"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        params = {"searchText": self._street_address}
        response = requests.post(
            "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/SearchAdress",
            params=params,
        )

        address_data = json.loads(response.text)
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

        entries = []
        for item in data["RhServices"]:
            waste_type = ""
            next_pickup = item["NextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            if item["WasteType"] == "FNI1":
                waste_type = (
                    "Kärl 1, "
                    + item["BinType"]["ContainerType"]
                    + " "
                    + str(item["BinType"]["Size"])
                    + item["BinType"]["Unit"]
                )
                icon = "mdi:trash-can"
            elif item["WasteType"] == "FNI2":
                waste_type = (
                    "Kärl 2, "
                    + item["BinType"]["ContainerType"]
                    + " "
                    + str(item["BinType"]["Size"])
                    + item["BinType"]["Unit"]
                )
                icon = "mdi:trash-can"
            elif item["BinType"]["Code"] == "KM140":
                waste_type = "Matpåsar"
                icon = "mdi:recycle"
            else:
                waste_type = (
                    item["WasteType"]
                    + " "
                    + item["BinType"]["ContainerType"]
                    + " "
                    + str(item["BinType"]["Size"])
                    + item["BinType"]["Unit"]
                )
                icon = "mdi:trash-can"
                if item["WasteType"] == "Trädgårdsavfall":
                    icon = "mdi:leaf"
            found = 0
            for x in entries:
                if x.date == next_pickup_date and x.type == waste_type:
                    found = 1
            if found == 0:
                entries.append(
                    Collection(date=next_pickup_date, t=waste_type, icon=icon)
                )
        return entries
