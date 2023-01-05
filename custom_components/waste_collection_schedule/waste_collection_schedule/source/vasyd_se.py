import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "VA Syd Sophämntning"
DESCRIPTION = "Source for VA Syd waste collection."
URL = "https://www.vasyd.se"
TEST_CASES = {
    "Home": {"street_address": "Industrigatan 13, Malmö"},
    "Polisen": {"street_address": "Drottninggatan 20, Malmö"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        data = {"query": self._street_address}
        response = requests.post(
            "https://www.vasyd.se/api/sitecore/MyPagesApi/BuildingAddressSearch",
            data=data,
        )

        building_data = json.loads(response.text)["items"]
        building_id = None
        if building_data and len(building_data) > 0:
            building_id = building_data[0]["id"]

        if not building_id:
            return []

        data = {"query": building_id, "street": self._street_address}
        response = requests.post(
            "https://www.vasyd.se/api/sitecore/MyPagesApi/WastePickupByAddress",
            data=data,
        )

        data = json.loads(response.text)["items"]

        entries = []
        for item in data:
            waste_type = item["wasteType"]
            icon = "mdi:trash-can"
            if waste_type == "Trädgårdsavfall":
                icon = "mdi:leaf"
            next_pickup = item["nextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
