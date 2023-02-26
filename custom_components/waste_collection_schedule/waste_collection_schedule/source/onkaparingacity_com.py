from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Onkaparinga Council"
DESCRIPTION = "Source for City of Onkaparinga Council, Australia."
URL = "https://www.onkaparingacity.com/"
COUNTRY = "au"
TEST_CASES = {
    "TestcaseI": {"address": "18 Flagstaff Road, FLAGSTAFF HILL 5159"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling Waste": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}

API_URL = "https://www.onkaparingacity.com"
HEADERS = {"referer": f"{API_URL}/Services/Waste-and-recycling/Bin-collections"}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):

        params = {"keywords": self._address}

        r = requests.get(
            f"{API_URL}/api/v1/myarea/search", params=params, headers=HEADERS
        )
        r.raise_for_status()

        addresses = r.json()

        if addresses == 0:
            raise Exception("address not found")

        params = {"geolocationid": addresses["Items"][0]["Id"], "ocsvclang": "en-AU"}

        r = requests.get(
            f"{API_URL}/ocapi/Public/myarea/wasteservices",
            params=params,
            headers=HEADERS,
        )
        r.raise_for_status()

        waste = r.json()

        soup = BeautifulSoup(waste["responseContent"], "html.parser")

        waste_type = []

        for tag in soup.find_all("h3"):
            if tag.text.startswith("Calendar"):
                continue
            waste_type.append(tag.text)

        waste_date = []
        for tag in soup.find_all("div", {"class": "next-service"}):
            tag_text = tag.text.strip()
            if tag_text != "":
                date_object = datetime.strptime(tag_text, "%a %d/%m/%Y").date()
                waste_date.append(date_object)

        waste = list(zip(waste_type, waste_date))

        entries = []
        for item in waste:
            entries.append(Collection(item[1], item[0], icon=ICON_MAP.get(item[0])))
        return entries
