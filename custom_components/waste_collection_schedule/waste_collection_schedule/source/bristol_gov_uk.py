# Credit where it's due:
# This is predominantly a refactoring of the Bristol City Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData

import re
import requests

# from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bristol City Council"
DESCRIPTION = "Source for bristol.gov.uk services for Bristol City Council, UK."
URL = "https://bristol.gov.uk"

TEST_CASES = {
    "Test_001": {"property": "6328436"},
    "Test_002": {"property": "6146611"},
    "Test_003": {"property": 6328436},
}
ICON_MAP = {
    "NON-RECYCLABLE REFUSE": "mdi:trash-can",
    "FOOD WASTE": "mdi:food",
    "GARDEN WASTE": "mdi:leaf",
    "PAPER & CARDBOARD": "mdi:newspaper",
    "MIXED RECYCLING (CANS, PLASTICS & GLASS)": "mdi:glass-fragile",
}
REGEX = {
    "waste": r'\"containerName\":\"([0-9]{2,3}L\s[a-zA-z\s]*)',
    "date": r'\"nextCollectionDate\":\"([\d]{4}-[\d]{2}-[\d]{2})'
}
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Connection": "keep-alive",
    "Ocp-Apim-Subscription-Key": "47ffd667d69c4a858f92fc38dc24b150",
    "Ocp-Apim-Trace": "true",
    "Origin": "https://bristolcouncil.powerappsportals.com",
    "Referer": "https://bristolcouncil.powerappsportals.com/",
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

        # Initialise form
        payload = {"servicetypeid": "7dce896c-b3ba-ea11-a812-000d3a7f1cdc"}
        response = s.get(
            "https://bristolcouncil.powerappsportals.com/completedynamicformunauth/",
            headers=HEADERS,
            params=payload,
        )

        # Set the search criteria
        payload = {"Uprn": "UPRN" + uprn}
        response = s.post(
            "https://bcprdapidyna002.azure-api.net/bcprdfundyna001-llpg/DetailedLLPG",
            headers=HEADERS,
            json=payload,
        )

        # Retrieve the schedule
        payload = {"uprn": uprn}
        response = s.post(
            "https://bcprdapidyna002.azure-api.net/bcprdfundyna001-alloy/NextCollectionDates",
            headers=HEADERS,
            json=payload,
        )

        waste_col = re.findall(REGEX["waste"], response.text)
        date_col = re.findall(REGEX["date"], response.text)

        print(waste_col)
        print(date_col)

        entries = []
        for item in date_collection:
            entries.append(
                Collection(
                    date=item[1],
                    t=item[0],
                    icon=ICON_MAP.get(item[0].upper()),
                )
            )

        return entries
