from datetime import datetime

import requests

import re
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Kungälvs kommun Avfallshantering"
DESCRIPTION = "Source script for kungalv.se"
URL = "https://www.kungalv.se/Bygga--bo--miljo/avfall-och-atervinning/avfall-fran-hushall/"
TEST_CASES = {
    "Komministergatan": {"street_address": "Komministergatan 4, Kungälv"}, 
    "Violgatan": {"street_address": "Violgatan 8, Ytterby"},
}

API_URL = "https://minasidor-va-avfall.kungalv.se/FutureWeb/SimpleWastePickup"

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:food-apple",
    "Förpackningar": "mdi:package-variant",
    "Metallförp.": "mdi:nail",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Street address for waste collection, including city.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street address",
    },
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        # Search for address
        response = requests.post(
            f"{API_URL}/SearchAdress",
            data={"searchText": self._street_address},
            timeout=30,
        )
        response.raise_for_status()

        address_data = response.json()
        if not address_data.get("Succeeded") or not address_data.get("Buildings"):
            raise SourceArgumentException("Failed to get schedule for ", self._street_address)

        # Extract building ID from first result (format: "Address, CITY (ID)")
        building = address_data["Buildings"][0]
        match = re.search(r"\((\d+)\)", building)
        if not match:
            raise SourceArgumentException("Could not extract building ID from result.", self._street_address)

        building_id = match.group(1)

        # Get waste pickup schedule
        response = requests.get(
            f"{API_URL}/GetWastePickupSchedule",
            params={"address": f"({building_id})"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        entries = []
        for item in data.get("RhServices", []):
            next_pickup = item.get("NextWastePickup")
            if not next_pickup:
                continue

            waste_type = item.get("WasteType", "")
            next_pickup_date = datetime.strptime(next_pickup, "%Y-%m-%d").date()

            entries.append(
                Collection(
                    date=next_pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                )
            )

        return entries
