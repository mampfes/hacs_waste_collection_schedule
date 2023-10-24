from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Lake Macquarie City Council"
DESCRIPTION = "Source for Lake Macquarie City Council, Australia."
URL = "https://www.lakemac.com.au/"
TEST_CASES = {
    "TestcaseI": {"address": "te"},
    "TestcaseII": {"address": "386 Pacific Highway, MURRAYS BEACH NSW 2281"},
}

ICON_MAP = {
    "General waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green waste": "mdi:leaf",
    "Bulk waste": "mdi:trash-can",
}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        url = "https://www.lakemac.com.au/api/v1/myarea/search"

        headers = {
            "referer": "https://www.lakemac.com.au/For-residents/Waste-and-recycling/When-are-your-bins-collected"
        }

        params = {"keywords": self._address}

        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()

        addresses = r.json()

        if addresses == 0:
            raise Exception("address not found")

        url = "https://www.lakemac.com.au/ocapi/Public/myarea/wasteservices"

        params = {"geolocationid": addresses["Items"][0]["Id"], "ocsvclang": "en-AU"}

        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        waste = r.json()

        soup = BeautifulSoup(waste["responseContent"], "html.parser")

        waste_type = []

        for tag in soup.find_all("h3"):
            waste_type.append(tag.text)

        waste_date = []
        for tag in soup.find_all("div", {"class": "next-service"}):
            try:
                date_object = datetime.strptime(tag.text.strip(), "%a %d/%m/%Y").date()
            except:
                continue    
            waste_date.append(date_object)

        waste = list(zip(waste_type, waste_date))

        entries = []
        for item in waste:
            entries.append(Collection(item[1], item[0], icon=ICON_MAP.get(item[0])))

        return entries
