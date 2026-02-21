import datetime
import json

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "City of Ryde (NSW)"
DESCRIPTION = "Source for City of Ryde rubbish collection."
URL = "https://www.ryde.nsw.gov.au/"
TEST_CASES = {
    "Ryde Aquatic Centre": {
        "post_code": "2112",
        "suburb": "Ryde",
        "street_name": "Victoria Road",
        "street_number": "504",
    },
    "Harris Farm Markets Boronia Park": {
        "post_code": "2111",
        "suburb": "Gladesville",
        "street_name": "Pittwater Road",
        "street_number": "128",
    },
    "Eastwood Shopping Centre": {
        "post_code": "2122",
        "suburb": "Eastwood",
        "street_name": "Rowe Street",
        "street_number": "152",
    },
}

API_URLS = {
    "address_search": "https://www.ryde.nsw.gov.au/api/v1/myarea/search",
    "collection": "https://www.ryde.nsw.gov.au/ocapi/Public/myarea/wasteservices",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.ryde.nsw.gov.au/Environment-and-Waste/Waste-and-Recycling",
    "X-Requested-With": "XMLHttpRequest",
}

ICON_MAP = {
    "General Waste": "trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}


class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str
    ):
        self.post_code = post_code
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):
        locationId = 0

        address = "{} {} {} {}".format(
            self.street_number, self.street_name, self.suburb, self.post_code
        )

        # Retrieve suburbs
        r = requests.get(
            API_URLS["address_search"], params={"keywords": address}, headers=HEADERS
        )

        data = json.loads(r.text)

        # Find the ID for our suburb
        for item in data["Items"]:
            locationId = item["Id"]
            break

        if locationId == 0:
            raise Exception(
                f"Could not find address: {self.street_number} {self.street_name}, {self.suburb} {self.post_code}"
            )

        # Retrieve the upcoming collections for our property
        r = requests.get(
            API_URLS["collection"],
            params={"geolocationid": locationId, "ocsvclang": "en-AU"},
            headers=HEADERS,
        )

        data = json.loads(r.text)

        responseContent = data["responseContent"]

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []

        for item in services:
            # test if <div> contains a valid date. If not, is is not a collection item.
            date_text = item.find("div", attrs={"class": "next-service"})

            # The date format currently used on https://www.ryde.nsw.gov.au/Environment-and-Waste/Waste-and-Recycling
            date_format = "%a %d/%m/%Y"

            try:
                # Strip carriage returns and newlines out of the HTML content
                cleaned_date_text = (
                    date_text.text.replace("\r", "").replace("\n", "").strip()
                )

                # Parse the date
                date = datetime.datetime.strptime(cleaned_date_text, date_format).date()

            except ValueError:
                continue

            waste_type = item.find("h3").text.strip()

            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                )
            )

        return entries
