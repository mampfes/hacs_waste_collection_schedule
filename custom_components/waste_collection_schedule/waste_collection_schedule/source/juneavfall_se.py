from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Jönköping - June Avfall & Miljö"
DESCRIPTION = "Source for June Avfall & Miljö waste collection."
URL = "https://www.juneavfall.se"
TEST_CASES = {
    "Storgatan 12": {"street_address": "Storgatan 12, Huskvarna"},
    "Smedjegatan 20": {"street_address": "Smedjegatan 20, Jönköping"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        r = requests.post(
            "https://minasidor.juneavfall.se/FutureWebJuneBasic/SimpleWastePickup/SearchAdress",
            {"searchText": self._street_address}
        )
        r.raise_for_status()

        address_data = r.json()
        address = None
        if address_data["Succeeded"] is True:
            if len(address_data["Buildings"]) > 0:
                address = address_data["Buildings"][0]

        if address is None:
            raise Exception("address not found")

        params = {"address": address}
        r = requests.get(
            "https://minasidor.juneavfall.se/FutureWebJuneBasic/SimpleWastePickup/GetWastePickupSchedule",
            params=params
        )
        r.raise_for_status()

        data = r.json()

        entries = []
        for item in data["RhServices"]:
            waste_type = item["WasteType"]
            icon = "mdi:trash-can"
            if waste_type == "Matavfall":
                icon = "mdi:leaf"
            next_pickup = item["NextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            entries.append(
                Collection(date=next_pickup_date, t=waste_type, icon=icon)
            )

        return entries
