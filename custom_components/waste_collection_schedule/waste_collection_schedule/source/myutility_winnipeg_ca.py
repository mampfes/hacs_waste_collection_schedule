import datetime
import requests
from waste_collection_schedule import Collection

# Constants for the Winnipeg Utility Billing Service
TITLE = "Winnipeg Utility Billing Service"
DESCRIPTION = "Source script for https://myutility.winnipeg.ca Use the same address as that works on the website under 'Find your collection day'"
URL = "https://myutility.winnipeg.ca"
TEST_CASES = {
    "TestWinnipeg": {"address": "123 EASY ST"},
}

# API URL for fetching collection management details
API_URL = "https://myutility.winnipeg.ca/UtilityBillingService/CollectionManagement/getCollectionManagementDetails?address="

# Mapping icons to different waste types for visual representation
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Garbage": "mdi:trash-can",
    "Yard Waste": "mdi:leaf"  # Icon for "Yard Waste"
}

class Source:
    def __init__(self, address):  
        # Format address for API call: replace spaces with '%20' and convert to uppercase
        self._address = address.replace(' ', '%20')
        self._address = self._address.upper()

    def fetch(self):
        # Perform API request using the formatted address
        response = requests.get(API_URL + self._address)
        data = response.json()

        # Check if 'Address' key is present in data; return empty list if not
        if 'Address' not in data:
            raise Exception("Address is not found")
            return []

        # Get eligible waste types for the address
        eligible_waste_types = self.get_eligible_waste_types(data)

        entries = []

        # Loop through each pickup date detail
        for detail in data["Address"]["PickUpDateDetails"]:
            # Loop through each waste type in the pickup date detail
            for waste in detail["WasteTypes"]:
                waste_type = waste["WasteType"]
                waste_type_code = waste["WasteTypeCode"]

                # Remove ' - A' suffix from waste type if present
                if " - A" in waste_type:
                    waste_type = waste_type.replace(" - A", "")

                # Check if waste type code is in the list of eligible waste types
                if waste_type_code in eligible_waste_types:
                    # Append collection entry with date, type, and icon
                    entries.append(
                        Collection(
                            date=datetime.date.fromisoformat(detail["Date"]),
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )
        return entries

    def get_eligible_waste_types(self, data):
        eligible_waste_type_codes = set()
        # Extract waste type codes from 'EligibleCollectionEventList'
        for event in data["Address"].get("EligibleCollectionEventList", []):
            eligible_waste_type_codes.add(event["WasteTypeCode"])

        return eligible_waste_type_codes
