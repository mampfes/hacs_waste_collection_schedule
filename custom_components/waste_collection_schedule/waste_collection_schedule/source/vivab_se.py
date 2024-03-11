import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "VIVAB Sophämtning"
DESCRIPTION = "Source for VIVAB waste collection."
URL = "https://www.vivab.se"
TEST_CASES = {
    "Gallerian": {"street_address": "Västra Vallgatan 2, Varberg"},
    "Polisen": {"street_address": "Östra Långgatan 5, Varberg"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        search_data = {"searchText": self._street_address}
        response = requests.post(
            "https://minasidor.vivab.info/FutureWebVarberg/SimpleWastePickup/SearchAdress",
            data=search_data,
        )

        building_data = json.loads(response.text)
        if not (
            building_data
            and "Succeeded" in building_data
            and "Buildings" in building_data
            and len(building_data["Buildings"]) > 0
        ):
            return []

        building_id = None

        # support only first building match
        building_id_matches = re.findall(r"\(([0-9]+)\)", building_data["Buildings"][0])
        if not building_id_matches or len(building_id_matches) == 0:
            return []
        building_id = building_id_matches[0]

        response = requests.get(
            f"https://minasidor.vivab.info/FutureWebVarberg/SimpleWastePickup/GetWastePickupSchedule?address=({building_id})"
        )

        waste_data = json.loads(response.text)
        if not ("RhServices" in waste_data and len(waste_data["RhServices"]) > 0):
            return []

        data = waste_data["RhServices"]

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
