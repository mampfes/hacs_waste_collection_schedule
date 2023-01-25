from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import json
import requests

TITLE = "Region Gotland"
DESCRIPTION = "Source for Region Gotland waste collection."
URL = "https://gotland.se"
TEST_CASES = {
    "TestService": {"uprn": "16903059805"},
}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:leaf"
}

class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        query_params = {"address": "(" + self._uprn + ")"}
        response = requests.get(
            "https://edpfuture.gotland.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule",
            params=query_params
        )
        data = json.loads(response.text)

        entries = []
        for item in data["RhServices"]:
            if item["WasteType"] == "Slam":
                continue

            next_pickup = item["NextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            waste_type = item["WasteType"]
            icon = ICON_MAP.get(waste_type)
            entries.append(
                Collection(date=next_pickup_date, t=waste_type, icon=icon)
            )

        return entries
