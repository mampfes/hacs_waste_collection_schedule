import datetime
import json

import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri
from waste_collection_schedule import Collection

TITLE = "Unley City Council (SA)"
DESCRIPTION = "Source for Unley City Council rubbish collection."
URL = "https://www.unley.sa.gov.au/"
TEST_CASES = {
    "Bible College of South Australia": {
        "post_code": "5061",
        "suburb": "Malvern",
        "street_name": "Wattle Street",
        "street_number": "176",
    },
    "291 on Unley": {
        "post_code": 5061,
        "suburb": "Unley",
        "street_name": "Unley Road",
        "street_number": "291",
    },
    "Consulate of Switzerland": {
        "post_code": "5063",
        "suburb": "Parkside",
        "street_name": "Castle Street",
        "street_number": 64,
    },
}

API_URLS = {
    "address_search": "https://www.unley.sa.gov.au/api/v1/myarea/search?keywords={}",
    "collection": "https://www.unley.sa.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU",
}

HEADERS = {"user-agent": "Mozilla/5.0"}

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

        address = "{} {} {} SA {}".format(
            self.street_number, self.street_name, self.suburb, self.post_code
        )

        q = requote_uri(str(API_URLS["address_search"]).format(address))

        # Retrieve suburbs
        r = requests.get(q, headers=HEADERS)

        data = json.loads(r.text)

        # Find the ID for our suburb
        for item in data["Items"]:
            locationId = item["Id"]
            break

        if locationId == 0:
            return []

        # Retrieve the upcoming collections for our property
        q = requote_uri(str(API_URLS["collection"]).format(locationId))

        r = requests.get(q, headers=HEADERS)

        data = json.loads(r.text)

        responseContent = data["responseContent"]

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []

        for item in services:
            # test if <div> contains a valid date. If not, is is not a collection item.
            date_text = item.find("div", attrs={"class": "next-service"})
            
            # The date format currently used on https://www.unley.sa.gov.au/Bins-pets-parking/Waste-recycling/Rubbish-collection-dates
            date_format = '%a %d/%m/%Y'

            try:
                # Strip carriage returns and newlines out of the HTML content
                cleaned_date_text = date_text.text.replace('\r','').replace('\n','').strip()

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
