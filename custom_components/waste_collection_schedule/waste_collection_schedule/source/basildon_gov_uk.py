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
    "Test_001": {"uprn": "100090277795"},
    "Test_002": {"uprn": "10024197625"},
    "Test_003": {"uprn": "10090455610"}
}
ICON_MAP = {
    "green_waste": "mdi:leaf",
    "general_waste": "mdi:trash-can",
    "food_waste": "mdi:food",
    "glass_waste": "mdi:bottle-wine",
    "papercard_waste": "mdi:package-varient",
    "plasticcans_waste": "mdi:bottle-soda-classic"
}
NAME_MAP = {
    "green_waste": "Garden",
    "general_waste": "General",
    "food_waste": "Food",
    "glass_waste": "Glass",
    "papercard_waste": "Paper/Cardboard",
    "plasticcans_waste": "Plastic/Cans"
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
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()

        # Retrieve the schedule
        payload = {"uprn": self._uprn}
        response = s.post(
            "https://basildonportal.azurewebsites.net/api/getPropertyRefuseInformation",
            headers=HEADERS,
            json=payload,
        )
        data = response.json()['refuse']['available_services']
        entries = []
        for item in ICON_MAP:
            for collection_date_key in ["current_collection_", "next_collection_", "last_collection_"]:
                if data[item][collection_date_key + "active"]:
                    date_string = data[item][collection_date_key + "date"]
                    entries.append(
                        Collection(
                            date=datetime.strptime(
                                date_string,
                                "%Y-%m-%d",
                            ).date(),
                            t=NAME_MAP[item],
                            icon=ICON_MAP.get(item.upper()),
                        )
                    )

        return entries