import datetime
import json

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Hume City Council"
DESCRIPTION = "Source for hume.vic.gov.au Waste Collection Services"
URL = "https://hume.vic.gov.au"
TEST_CASES = {
    "19 Potter": {
        "post_code": "3064",
        "suburb": "Craigieburn",
        "street_name": "Potter Street",
        "street_number": "19",
    },
    "1/90 Vineyard": {
        "post_code": "3429",
        "suburb": "Sunbury",
        "street_name": "Vineyard Road",
        "street_number": "1/90",
    },
    "9-19 McEwen": {
        "post_code": "3429",
        "suburb": "Sunbury",
        "street_name": "McEwen Drive",
        "street_number": "9-19",
    },
    "33 Toyon": {
        "post_code": "3064",
        "suburb": "Kalkallo",
        "street_name": "Toyon Road",
        "street_number": "33",
    },
}

API_URLS = {
    "address_search": "https://www.hume.vic.gov.au/api/v1/myarea/search",
    "collection": "https://www.hume.vic.gov.au/ocapi/Public/myarea/wasteservices",
}

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.hume.vic.gov.au/Residents/Waste/Know-my-bin-day",
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food and garden": "mdi:leaf",
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

            # The date format currently used on https://www.hume.vic.gov.au/Residents/Waste/Know-my-bin-day
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
