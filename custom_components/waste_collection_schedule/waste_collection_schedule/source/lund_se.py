import json
from datetime import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Lund Waste Collection"
DESCRIPTION = "Source for Lund waste collection services, Sweden."
URL = "https://eservice431601.lund.se"
TEST_CASES = {
    "Home": {"street_address": "Your Street Address Here"},
    # Add more test cases as needed
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}

class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        s = requests.Session()

        # Search for the address ID
        search_payload = {'searchText': self._street_address}
        search_response = s.post(
            "https://eservice431601.lund.se/Lund/FutureWeb/SimpleWastePickup/SearchAdress",
            json=search_payload,
            headers=HEADERS,
        )
        search_data = json.loads(search_response.text)

        # Check if the search was successful
        if search_data.get("Succeeded", False):
            address_id = search_data["Buildings"][0] if search_data["Buildings"] else None

            if address_id:
                # Retrieve waste collection schedule
                schedule_url = f"https://eservice431601.lund.se/Lund/FutureWeb/SimpleWastePickup/GetWastePickupSchedule?address={address_id}"
                schedule_response = s.get(schedule_url, headers=HEADERS)
                schedule_data = json.loads(schedule_response.text)

                entries = []
                for service in schedule_data.get("RhServices", []):
                    waste_type = service.get("WasteType", "")
                    icon = "mdi:trash-can"  # Default icon
                    # You may need to adjust the mapping based on the actual response data
                    # This is just a placeholder, adjust according to Lund API response

                    next_pickup = service.get("NextWastePickup", "")
                    next_pickup_date = datetime.fromisoformat(next_pickup).date()

                    entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

                return entries
            else:
                print(f"Failed to get address ID for {self._street_address}.")
        else:
            print(f"Search for address failed for {self._street_address}.")
