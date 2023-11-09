import datetime
import json

import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Blacktown City Council (NSW)"
DESCRIPTION = "Source for Blacktown City Council rubbish collection."
URL = "https://www.blacktown.nsw.gov.au/"
TEST_CASES = {
    "Plumpton Marketplace": {
        "post_code": "2761",
        "suburb": "Plumpton",
        "street_name": "Jersey Rd",
        "street_number": "260",
    },
    "Rooty Hill Tennis & Squash Centre": {
        "post_code": "2766",
        "suburb": "Rooty Hill",
        "street_name": "Learmonth St",
        "street_number": "13-15",
    },
    "Workers Blacktown": {
        "post_code": "2148",
        "suburb": "Blacktown",
        "street_name": "Campbell St",
        "street_number": "55",
    },
    "Hythe St": {
        "post_code": "2770",
        "suburb": "Mount Druitt",
        "street_name": "Hythe St",
        "street_number": "9-11",
    },
}

API_URLS = {
    "address_search": "https://www.blacktown.nsw.gov.au/api/v1/myarea/search?keywords={}",
    "collection": "https://www.blacktown.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU",
}

HEADERS = {"user-agent": "Mozilla/5.0"}

ICON_MAP = {
    "General Waste": "trash-can",
    "Recycling": "mdi:recycle",
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

        address = "{} {} {} NSW {}".format(
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
            raise ValueError(
                f"Unable to find location ID for {address}, maybe you misspelled your address?"
            )

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

            # The date format currently used on https://www.blacktown.nsw.gov.au/Services/Waste-services-and-collection/Waste-collection-days
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
