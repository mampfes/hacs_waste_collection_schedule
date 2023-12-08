import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Lund Waste Collection"
DESCRIPTION = "Source for Lund waste collection services, Sweden."
URL = "https://eservice431601.lund.se"
TEST_CASES = {
    "Lokföraregatan 7": {"street_address": "Lokföraregatan 7, LUND (19120)"},
    "Annedalsvägen 2 B": {"street_address": "Annedalsvägen 2 B, LUND (39037)"},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Plastförpacknin": "mdi:recycle",
    "Tidningar": "mdi:newspaper",
    "Metallförpackni": "mdi:recycle",
    "Matavfall": "mdi:food-apple",
    "Ofärgat Glas": "mdi:glass-wine",
    "Färgat Glas": "mdi:glass-wine",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        s = requests.Session()

        # Search for the address ID
        search_payload = {"searchText": self._street_address.split("(")[0].strip()}
        search_response = s.post(
            "https://eservice431601.lund.se/Lund/FutureWeb/SimpleWastePickup/SearchAdress",
            json=search_payload,
            headers=HEADERS,
        )
        search_data = json.loads(search_response.text)

        # Check if the search was successful
        if not search_data.get("Succeeded", False):
            raise ValueError(f"Search for address failed for {self._street_address}.")

        address_id = search_data["Buildings"][0] if search_data["Buildings"] else None
        if not address_id:
            raise ValueError(f"Failed to get address ID for {self._street_address}.")

        # Retrieve waste collection schedule
        schedule_url = f"https://eservice431601.lund.se/Lund/FutureWeb/SimpleWastePickup/GetWastePickupSchedule?address={address_id}"
        schedule_response = s.get(schedule_url, headers=HEADERS)
        schedule_data = json.loads(schedule_response.text)

        entries = []
        for service in schedule_data.get("RhServices", []):
            waste_type = service.get("WasteType", "")

            next_pickup = service.get("NextWastePickup", "")
            next_pickup_date = datetime.fromisoformat(next_pickup).date()

            entries.append(
                Collection(
                    date=next_pickup_date, t=waste_type, icon=ICON_MAP.get(waste_type)
                )
            )

        return entries
