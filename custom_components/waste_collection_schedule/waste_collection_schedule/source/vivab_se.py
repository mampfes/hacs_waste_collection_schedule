import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "VIVAB Sophämtning"
DESCRIPTION = "Source for VIVAB waste collection."
URL = "https://www.vivab.se"
TEST_CASES = {
    "Varberg: Gallerian": {"street_address": "Västra Vallgatan 2, Varberg"},
    "Varberg: Polisen": {"street_address": "Östra Långgatan 5, Varberg"},
    "Falkenberg: Storgatan 1": {"street_address": "Storgatan 1, FALKENBERG"},
    "Falkenberg: Östergränd 4": {"street_address": "Östergränd 4, Falkenberg"},
}

API_URLS = {
    "falkenberg": "https://minasidor.vivab.info/FutureWebFalken/SimpleWastePickup/",
    "varberg": "https://minasidor.vivab.info/FutureWebVarberg/SimpleWastePickup/",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address
        region = None
        if "falkenberg" in street_address.lower():
            region = "falkenberg"
        elif "varberg" in street_address.lower():
            region = "varberg"
        if region is None:
            raise ValueError(
                "Address not supported should end with ', Varberg' or ', Falkenberg'"
            )
        self._api_url = API_URLS[region]

    def fetch(self):
        search_data = {"searchText": self._street_address.split(",")[0].strip()}

        response = requests.post(
            f"{self._api_url}SearchAdress",
            data=search_data,
        )

        building_data = json.loads(response.text)
        if not (
            building_data
            and "Succeeded" in building_data
            and "Buildings" in building_data
            and len(building_data["Buildings"]) > 0
        ):
            raise ValueError("No building found")

        building_id = None

        # support only first building match
        building_id_matches = re.findall(r"\(([0-9]+)\)", building_data["Buildings"][0])
        if not building_id_matches or len(building_id_matches) == 0:
            raise ValueError("No building id found")
        building_id = building_id_matches[0]

        response = requests.get(
            f"{self._api_url}GetWastePickupSchedule",
            params={"address": f"({building_id})"},
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
