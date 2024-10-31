from datetime import datetime
from typing import List
import json
import requests


from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
# Include work around for SSL UNSAFE_LEGACY_RENEGOTIATION_DISABLED error
from waste_collection_schedule.service.SSLError import get_legacy_session

TITLE = "Thanet District Council"
DESCRIPTION = (
    "Source for thanet.gov.uk services for Thanet District Council"
)
URL = "https://thanet.gov.uk"

TEST_CASES = {
    "uprn": {"uprn": "100061108233"},
    "houseName": {"postcode": "CT7 9SL", "street_address": "Forus"},
    "houseNumber": {"postcode": "CT7 9SL", "street_address": "6 Gordon Square"},
}

TYPES = {
    "Refuse": {"icon": "mdi:trash-can", "alias": "Rubbish"},
    "BlueRecycling": {"icon": "mdi:recycle", "alias": "Mixed Recycling (Blue)"},
    "RedRecycling": {"icon": "mdi:note-multiple", "alias": "Paper & Card (Red)"},
    "Food": {"icon": "mdi:food-apple", "alias": "Food Waste"},
    "Garden": {"icon": "mdi:lead", "alias": "Garden"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Enter either your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/))"
    "OR Enter your postcode and the first line of your address for street address e.g. '2 London Road' (anything before the first comma)"
    "UPRNs should work all of the time, Postcodes and Street Addresses will work if a match can be found."
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "street_address": "House name OR Number and Street name",
        "postcode": "Postcode",
    }
}


class Source:
    
    header_text = { 'Accept-Language' :"en-GB,en;q=0.9,en-US;q=0.8",
            'User-Agent': "Mozilla/5.0",
            }
    
    
    def __init__(self, uprn=None, postcode=None, street_address=None):
        self._postcode = postcode
        self._street_address = str(street_address).upper()
        self._uprn = uprn

    def fetch(self) -> List[Collection]:
        if self._uprn is None:
            self._uprn = self.get_uprn()

        url = f"https://www.thanet.gov.uk/wp-content/mu-plugins/collection-day/incl/mu-collection-day-calls.php?pAddress={self._uprn}"
        collections_json = requests.get(url, headers= self.header_text).json()

        entries = []
        
        for collection in collections_json:
            for bin_type in TYPES:
                if collection["type"] == bin_type:
                    entries.append(
                        Collection(
                            date=datetime.strptime(collection['nextDate'][:10], "%d/%m/%Y").date(),
                            t=TYPES[bin_type]['alias'],
                            icon=TYPES[bin_type]['icon'],
                        )
                    )
                    entries.append(
                        Collection(
                            date=datetime.strptime(collection['previousDate'][:10], "%d/%m/%Y").date(),
                            t=TYPES[bin_type]['alias'],
                            icon=TYPES[bin_type]['icon'],
                        )
                    )
        return entries
        
    def get_uprn(self) -> str:
        url = f"https://www.thanet.gov.uk/wp-content/mu-plugins/collection-day/incl/mu-collection-day-calls.php?searchAddress={requests.utils.quote(self._postcode)}"
        addresses_json = requests.get(url, headers= self.header_text).json()
        uprn = next((key for key,
                     value in addresses_json.items() if value[:len(self._street_address)] == self._street_address),
                     None)
        if uprn is None:
                    raise SourceArgumentNotFoundWithSuggestions(
                        "Street Address",
                        self._street_address,
                        [value.split(",")[0] for value, value in addresses_json.items()],
                    )

        return uprn