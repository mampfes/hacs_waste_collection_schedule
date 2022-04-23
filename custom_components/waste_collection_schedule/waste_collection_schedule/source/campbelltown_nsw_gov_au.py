from bs4 import BeautifulSoup
import datetime
import json
import requests
from requests.utils import requote_uri
from waste_collection_schedule import Collection

TITLE = "Campbelltown City Council"
DESCRIPTION = "Source for Campbelltown City Council rubbish collection."
URL = "https://www.campbelltown.nsw.gov.au/"
TEST_CASES = {
    "Minto Mall": {
        "post_code": "2566",
        "suburb": "Minto",
        "street_name": "Brookfield Road",
        "street_number": "10",
    },
    "Campbelltown Catholic Club": {
        "post_code": "2560",
        "suburb": "Campbelltown",
        "street_name": "Camden Road",
        "street_number": "20-22",
    },
    "Australia Post Ingleburn": {
        "post_code": "2565",
        "suburb": "INGLEBURN",
        "street_name": "Oxford Road",
        "street_number": "34",
    },
}

API_URLS = {
    "address_search": "https://www.campbelltown.nsw.gov.au/ocsvc/public/spatial/findaddress?address={}",
    "collection": "https://www.campbelltown.nsw.gov.au/ocsvc/Public/InMyNeighbourhood/WasteServices?GeoLocationId={}",
}

HEADERS = {"user-agent": "Mozilla/5.0"}


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

        address = "{0} {1} {2} NSW {3}".format(
            self.street_number, self.street_name, self.suburb, self.post_code
        )

        q = requote_uri(str(API_URLS["address_search"]).format(address))

        # Retrieve suburbs
        r = requests.get(q, headers=HEADERS)

        data = json.loads(r.text)

        # Find the ID for our suburb
        for item in data["locations"]:
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
        services = soup.find_all("div", attrs={"class": "service-details"})

        entries = []

        for item in services:
            collectionDate = item.find("span")
            try:
                dateConverted = datetime.datetime.strptime(
                    collectionDate.text, "%A%d %b %Y"
                ).date()
            except:
                dateConverted = ""
            else:
                if "General Waste" in item.text:
                    entries.append(
                        Collection(
                            date=dateConverted, t="General Waste", icon="mdi:trash-can"
                        )
                    )

                if "Recycling" in item.text:
                    entries.append(
                        Collection(
                            date=dateConverted, t="Recycling", icon="mdi:recycle"
                        )
                    )

                if "Green Waste" in item.text:
                    entries.append(
                        Collection(date=dateConverted, t="Green Waste", icon="mdi:leaf")
                    )

        return entries
