import json
import urllib
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Kristianstad Renhållning"
DESCRIPTION = "Source for Kristianstad Renhållning waste collection."
URL = "https://renhallningen-kristianstad.se"
TEST_CASES = {
    "Case_0": {"street_address": "Östra Boulevarden 1"},
    "Case_1": {"street_address": "Grenadjärvägen 1"},
    "Case_2": {"street_address": "Skogsvägen 18"},
    "Case_3": {"street_address": "Önnestadsvägen 7"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        params = [{"query": self._street_address}]
        headers = {"Module": "universal", 
                   "Accept": "application/json, text/plain, */*", 
                   "Unit": "dd905ce7-b16d-4422-be36-564169af4035"}
        response = requests.get(
            "https://api-universal.appbolaget.se/waste/addresses/search",
            headers=headers,
            params=urllib.parse.urlencode(params),
        )

        building_data = json.loads(response.text)["data"]
        building_id = None
        if building_data and len(building_data) > 0:
            building_id = building_data[0]["uuid"]

        if not building_id:
            return []

        params = [building_id]
        headers = {"Module": "universal", 
                   "Accept": "application/json, text/plain, */*", 
                   "Unit": "dd905ce7-b16d-4422-be36-564169af4035"}
        response = requests.get(
            "https://api-universal.appbolaget.se/waste/addresses",
            headers=headers,
            params=urllib.parse.urlencode(params),
        )

        data = json.loads(response.text)["services"]

        entries = []
        for item in data:
            waste_type = item["type"]
            icon = "mdi:trash-can"
            if waste_type == "Trädgårdsavfall":
                icon = "mdi:leaf"
            next_pickup = item["collection_at"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
