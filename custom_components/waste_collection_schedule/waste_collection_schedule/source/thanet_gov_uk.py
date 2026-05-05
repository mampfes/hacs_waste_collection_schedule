from datetime import datetime
from typing import List

from curl_cffi import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Thanet District Council"
DESCRIPTION = "Source for thanet.gov.uk services for Thanet District Council"
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
    "Garden": {"icon": "mdi:leaf", "alias": "Garden"},
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
    def __init__(self, uprn=None, postcode=None, street_address=None):
        self._postcode = postcode
        self._street_address = str(street_address).upper()
        self._uprn = uprn
        self._session = requests.Session(impersonate="chrome124")

    def fetch(self) -> List[Collection]:
        if self._uprn is None:
            self._uprn = self.get_uprn()

        url = "https://www.thanet.gov.uk/wp-content/mu-plugins/collection-day/incl/mu-collection-day-calls.php"
        r = self._session.get(url, params={"pAddress": self._uprn}, timeout=30)
        r.raise_for_status()
        collections_json = r.json()

        entries = []

        for collection in collections_json:
            for bin_type in TYPES:
                if collection["type"] == bin_type:
                    entries.append(
                        Collection(
                            date=datetime.strptime(
                                collection["nextDate"][:10], "%d/%m/%Y"
                            ).date(),
                            t=TYPES[bin_type]["alias"],
                            icon=TYPES[bin_type]["icon"],
                        )
                    )
                    entries.append(
                        Collection(
                            date=datetime.strptime(
                                collection["previousDate"][:10], "%d/%m/%Y"
                            ).date(),
                            t=TYPES[bin_type]["alias"],
                            icon=TYPES[bin_type]["icon"],
                        )
                    )
        return entries

    def get_uprn(self) -> str:
        if self._postcode is None:
            raise SourceArgumentRequired(
                "postcode",
                "A postcode is required if no UPRN has been used. This allows the script to obtain the UPRN for you.",
            )
        url = "https://www.thanet.gov.uk/wp-content/mu-plugins/collection-day/incl/mu-collection-day-calls.php"
        r = self._session.get(url, params={"searchAddress": self._postcode}, timeout=30)
        r.raise_for_status()
        addresses_json = r.json()
        uprn = next(
            (
                key
                for key, value in addresses_json.items()
                if value[: len(self._street_address)] == self._street_address
            ),
            None,
        )
        if self._street_address is None:
            raise SourceArgumentRequiredWithSuggestions(
                "street_address",
                "A street address is needed, please select one from the list.",
                [value.split(",")[0] for value, value in addresses_json.items()],
            )
        if uprn is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "Street Address",
                self._street_address,
                [value.split(",")[0] for value, value in addresses_json.items()],
            )

        return uprn
