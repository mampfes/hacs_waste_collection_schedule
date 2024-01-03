# Credit where it's due:
# This is predominantly a refactoring of the Bristol City Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData

from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Basildon Council"
DESCRIPTION = "Source for basildon.gov.uk services for Basildon Council, UK."
URL = "https://basildon.gov.uk"

TEST_CASES = {
    "Test_Addres_001": {"postcode": "CM111BJ", "address": "6, HEADLEY ROAD"},
    "Test_Addres_002": {"postcode": "SS14 1QU", "address": "25 LONG RIDING"},
    "Test_UPRN_001": {"uprn": "100090277795"},
    "Test_UPRN_002": {"uprn": 10024197625},
    "Test_UPRN_003": {"uprn": "10090455610"},
}
ICON_MAP = {
    "green_waste": "mdi:leaf",
    "general_waste": "mdi:trash-can",
    "food_waste": "mdi:food",
    "glass_waste": "mdi:bottle-wine",
    "papercard_waste": "mdi:package-varient",
    "plasticcans_waste": "mdi:bottle-soda-classic",
}
NAME_MAP = {
    "green_waste": "Garden",
    "general_waste": "General",
    "food_waste": "Food",
    "glass_waste": "Glass",
    "papercard_waste": "Paper/Cardboard",
    "plasticcans_waste": "Plastic/Cans",
}
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Connection": "keep-alive",
    "Ocp-Apim-Trace": "true",
    "Origin": "https://mybasildon.powerappsportals.com",
    "Referer": "https://mybasildon.powerappsportals.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
}


class Source:
    def __init__(self, postcode=None, address=None, uprn=None):
        if uprn is None and (postcode is None or address is None):
            raise ValueError("Either uprn or postcode and address must be provided")

        self._uprn = str(uprn).zfill(12) if uprn is not None else None
        self._postcode = postcode
        self._address = address

    def compare_address(self, address) -> bool:
        return (
            self._address.replace(",", "").replace(" ", "").upper()
            == address.replace(",", "").replace(" ", "").upper()
        )

    def get_uprn(self, s):
        r = s.post(
            "https://basildonportal.azurewebsites.net/api/listPropertiesByPostcode",
            headers=HEADERS,
            json={"postcode": self._postcode},
        )
        r.raise_for_status()
        data = r.json()
        if data["result"] != "success":
            raise ValueError("Invalid postcode")
        for item in data["properties"]:
            if self.compare_address(item["line1"]):
                self._uprn = item["uprn"]
                break
        if self._uprn is None:
            raise ValueError("Invalid address")

    def fetch(self):
        s = requests.Session()
        if self._uprn is None:
            self.get_uprn(s)

        # Retrieve the schedule
        payload = {"uprn": self._uprn}
        response = s.post(
            "https://basildonportal.azurewebsites.net/api/getPropertyRefuseInformation",
            headers=HEADERS,
            json=payload,
        )
        data = response.json()["refuse"]["available_services"]
        entries = []
        for item in ICON_MAP:
            for collection_date_key in [
                "current_collection_",
                "next_collection_",
                "last_collection_",
            ]:
                if data[item][collection_date_key + "active"]:
                    date_string = data[item][collection_date_key + "date"]
                    entries.append(
                        Collection(
                            date=datetime.strptime(
                                date_string,
                                "%Y-%m-%d",
                            ).date(),
                            t=NAME_MAP[item],
                            icon=ICON_MAP.get(item),
                        )
                    )

        return entries
