import datetime
import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Ljusdal Energi"
DESCRIPTION = "Fetches waste collection schedules from Ljusdal Energi."
URL = "https://ljusdalenergi.se"
COUNTRY = "se"

# Public test case using Ljusdal Municipality Hall (Kommunhus) for automated validation
TEST_CASES = {
    "Ljusdal Kommunhus": {"address": "Norra Järnvägsgatan 21, Ljusdal"},
}

# Maps waste fractions to standard Home Assistant icons
ICON_MAP = {
    "Matavfall": Icons.FOOD_WASTE,
    "Restavfall": Icons.TRASH,
    "Hushållsavfall": Icons.TRASH,
    "Pappersförpackningar": Icons.PAPER_BAG,
    "Plastförpackningar": Icons.PLASTIC,
}

PARAM_DESCRIPTIONS = {
    "en": {"address": "Your street address and city (e.g., 'Norra Järnvägsgatan 21, Ljusdal')."},
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        
        # Step 1: Search for the address to obtain its unique ServiceId
        address_url = f"{URL}/api/waste/addresssearch"
        address_payload = {"searchString": self._address}
        
        response = session.post(address_url, json=address_payload)
        response.raise_for_status()
        address_data = response.json()
        
        if not address_data:
            raise SourceArgumentNotFound("address", self._address)
            
        # Handle if the API returns a list (as seen in the developer tools)
        if isinstance(address_data, list):
            if len(address_data) == 0:
                raise SourceArgumentNotFound("address", self._address)
            first_match = address_data[0]
        else:
            first_match = address_data
            
        # Extract ServiceId from the matching search result
        service_id = first_match.get("ServiceId")
        if not service_id:
            raise SourceArgumentNotFound("address", self._address)

        # Step 2: Fetch the collection calendar using the ServiceId
        calendar_url = f"{URL}/api/waste/getcollections"
        calendar_payload = {"serviceId": service_id}
        
        calendar_response = session.post(calendar_url, json=calendar_payload)
        calendar_response.raise_for_status()
        calendar_data = calendar_response.json()
        
        entries = []
        
        # Loop through the returned collection dates
        for item in calendar_data:
            waste_type = item.get("WasteType", "Hushållsavfall")
            date_str = item.get("CollectionDate")
            
            if not date_str:
                continue
                
            # Convert string to datetime.date object (strip time if present)
            date_clean = date_str.split("T")[0]
            pickup_date = datetime.datetime.strptime(date_clean, "%Y-%m-%d").date()
            
            # Match waste type to catalog icon, fallback to standard trash icon
            icon = ICON_MAP.get(waste_type, Icons.TRASH)
            
            entries.append(
                Collection(
                    date=pickup_date,
                    t=waste_type,
                    icon=icon
                )
            )
            
        return entries
