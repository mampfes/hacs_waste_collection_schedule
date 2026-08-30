from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Partille kommun"
DESCRIPTION = "Source for Partille kommun waste collection."
URL = "https://vatjanst.partille.se"
SOURCE_CODEOWNERS = ["@sadjad1"]

TEST_CASES = {
    "Partille kommunhus": {"street_address": "Gamla Kronvägen 34, Partille"},
}

SEARCH_URL = "https://vatjanst.partille.se/FutureWeb/SimpleWastePickup/SearchAdress"
SCHEDULE_URL = (
    "https://vatjanst.partille.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule"
)


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        r = requests.post(SEARCH_URL, {"searchText": self._street_address})
        r.raise_for_status()

        address_data = r.json()
        address = None

        if address_data["Succeeded"] is True and len(address_data["Buildings"]) > 0:
            address = address_data["Buildings"][0]

        if address is None:
            raise SourceArgumentNotFound("street_address", self._street_address)

        r = requests.get(SCHEDULE_URL, params={"address": address})
        r.raise_for_status()

        data = r.json()

        entries = []

        for item in data["RhServices"]:
            waste_type = item["WasteType"]
            next_pickup_date = datetime.fromisoformat(item["NextWastePickup"]).date()

            entries.append(
                Collection(
                    date=next_pickup_date,
                    t=waste_type,
                    icon=Icons.GENERAL_WASTE,
                )
            )

        return entries
