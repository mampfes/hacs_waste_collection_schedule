from datetime import datetime

import requests
import re
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bury Council"
DESCRIPTION = "Source for bury.gov.uk services for Bury Council, UK."
URL = "https://bury.gov.uk"

TEST_CASES = {
    "Test_Address_001": {"postcode": "bl81dd", "address": "2 Oakwood Close"}, 
    "Test_Address_002": {"postcode": "bl8 2sg", "address": "9, BIRKDALE DRIVE"},
    "Test_Address_003": {"postcode": "BL8 3DG", "address": "18, slaidburn drive"},
    "Test_ID_001": {"id": "649158"},
    "Test_ID_002": {"id": "593456"},

}
ICON_MAP = {
    "brown": "mdi:leaf",
    "grey": "mdi:trash-can",
    "green": "mdi:package-variant",
    "blue": "mdi:bottle-soda-classic",
}
NAME_MAP = {
    "brown": "Garden",
    "grey": "General",
    "green": "Paper/Cardboard",
    "blue": "Plastic/Cans/Glass",
}
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Connection": "keep-alive",
    "Ocp-Apim-Trace": "true",
    "Origin": "https://bury.gov.uk",
    "Referer": "https://bury.gov.uk",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
}


class Source:
    def __init__(self, postcode=None, address=None, id=None):
        if id is None and (postcode is None or address is None):
            raise ValueError("Postcode and address must be provided")

        self._id = str(id).zfill(6) if id is not None else None
        self._postcode = postcode
        self._address = address

    def compare_address(self, address) -> bool:
        return (
            self._address.replace(",", "").replace(" ", "").upper()
            == address.replace(",", "").replace(" ", "").upper()
        )

    def get_id(self, s):

        url = "https://www.bury.gov.uk/app-services/getProperties"
        params = {"postcode": self._postcode}

        r = s.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        if data["error"] == True:
            raise ValueError("Invalid postcode")
        for item in data["response"]:
            if self.compare_address(item["addressLine1"]):
                self._id = item["id"]
                break
        if self._id is None:
            raise ValueError("Invalid address")

    def fetch(self):
        s = requests.Session()
        if self._id is None:
            self.get_id(s)

        # Retrieve the schedule
        params = {"id": self._id}
        response = s.get(
            "https://www.bury.gov.uk/app-services/getPropertyById",
            headers=HEADERS,
            params=params,
        )
        data = response.json()

        # Define a regular expression pattern to match ordinal suffixes
        ordinal_suffix_pattern = r'(?<=\d)(?:st|nd|rd|th)'

        entries = []
        for bin_name, bin_info in data['response']['bins'].items():
            
            # Remove the ordinal suffix from the date string
            date_str_without_suffix = re.sub(ordinal_suffix_pattern, '', bin_info['nextCollection'])

            entries.append(
                Collection(
                    date=datetime.strptime(date_str_without_suffix, '%A %d %B %Y',).date(),
                    t=NAME_MAP[bin_name],
                    icon=ICON_MAP.get(bin_name),
                )
            )

        return entries
