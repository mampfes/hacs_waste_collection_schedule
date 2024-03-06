import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "VIVAB Sophämtning"
DESCRIPTION = "Source for VIVAB waste collection."
URL = "https://www.vivab.se"
TEST_CASES = {
    "Home": {"street_address": "Västra Vallgatan 2, Varberg"},
    "Polisen": {"street_address": "Östra Långgatan 5, Varberg"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        data = {"searchText": self._street_address}
        response = requests.post(
            "https://minasidor.vivab.info/FutureWebVarberg/SimpleWastePickup/SearchAdress",
            data=data,
        )

        building_data = json.loads(response.text)
        if not (
            building_data
            and "Succeeded" in building_data
            and building_data["Succeeded"]
        ):
            return []

        building_id = None
        if building_data and len(building_data) > 0:
            building_id = re.findall(r"\(([0-9]+)\)", building_data["Buildings"][0])[0]

        if not building_id:
            return []

        response = requests.get(
            f"https://minasidor.vivab.info/FutureWebVarberg/SimpleWastePickup/GetWastePickupSchedule?address=({building_id})"
        )

        data = json.loads(response.text)["RhServices"]

        entries = []
        for item in data:
            waste_type = item["WasteType"]
            icon = "mdi:trash-can"
            if waste_type == "Mat":
                icon = "mdi:food-apple"
            next_pickup = item["NextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
