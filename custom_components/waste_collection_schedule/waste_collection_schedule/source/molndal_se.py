from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mölndal"
DESCRIPTION = "Source for Mölndal waste collection."
URL = "https://molndal.se"
TEST_CASES = {
    "105000": {"facility_id": "105000"},
    "109400": {"facility_id": "109400"}
}

API_URL = "https://future.molndal.se/FutureWeb/SimpleWastePickup"


class Source:
    def __init__(self, facility_id: int):
        self.facility_id: str = str(facility_id)

    def fetch(self):
        url = f"{API_URL}/GetWastePickupSchedule"
        params={"address": f"({self.facility_id})"}
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        entries = []
        for item in data["RhServices"]:
            next_pickup = item["NextWastePickup"]
            if not next_pickup:
                continue

            next_pickup_date = datetime.strptime(next_pickup, "%Y-%m-%d").date()
            waste_type = item["WasteType"]

            entries.append(
                Collection(date=next_pickup_date, t=waste_type, icon="mdi:trash-can")
            )

        return entries

