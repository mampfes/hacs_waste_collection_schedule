import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Region Gotland"
DESCRIPTION = "Source for Region Gotland waste collection."
URL = "https://gotland.se"
TEST_CASES = {
    "TestService": {"uprn": "16903059805"},
}

ICON_MAP = {
    "Restavfall": Icons.GENERAL_WASTE,
    "Matavfall": Icons.BIO_KITCHEN,
    "Fyrfack 1": Icons.GENERAL_WASTE,
    "Fyrfack 2": Icons.RECYCLING,
}

class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        query_params = {"address": "(" + self._uprn + ")"}
        response = requests.get(
            "https://edpfuture.gotland.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule",
            params=query_params,
        )
        data = json.loads(response.text)

        entries = []
        for item in data["RhServices"]:
            if item["WasteType"] not in {"Restavfall", "Matavfall", "Fyrfack 1", "Fyrfack 2"}:
                continue

            next_pickup = item["NextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            waste_type = item["WasteType"]
            icon = ICON_MAP.get(waste_type)
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
