# import requests module
import requests

# Import json module to parse json output
import json

# Import Collection module to define for scheduler
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Import datetime to manipulate the time output from the site
from datetime import date, datetime

# Import BeautifulSoup to parse broken HTML from the site
from bs4 import BeautifulSoup

from urllib.parse import quote_plus

TITLE = "Gold Coast City Council"
DESCRIPTION = "Source for Gold Coast Council rubbish collection."
URL = "https://www.goldcoast.qld.gov.au"
TEST_CASES = {
    "MovieWorx": {
        "suburb": "Helensvale",
        "street_name": "Millaroo Dr",
        "street_number": "50",
    },
    "The Henchman": {
        "suburb": "Miami",
        "street_name": "Henchman Ave",
        "street_number": "6/8",
    },
    "Pie Pie": {
        "suburb": "Burleigh Heads",
        "street_name": "Gold Coast Hwy",
        "street_number": "1887",
    },
}

HEADERS = {"user-agent": "Mozilla/5.0"}

ICON_MAP = {   # Dict of waste types and suitable mdi icons
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "ORGANIC": "mdi:leaf",
}

class Source:
    def __init__(self, suburb, street_name, street_number):
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):

        today = date.today()

        # Construct the expected URL address
        siteAddress = quote_plus(f"{self.street_number} {self.street_name} {self.suburb}")
        # Making a get request
        response = requests.get(f'https://www.goldcoast.qld.gov.au/api/v1/myarea/searchfuzzy?keywords={siteAddress}&maxresults=1')
        data = json.loads(response.text)

        # Sort through the json to get the Geocoding GUID for the address
        for item in data["Items"]:
            siteId = item["Id"]
            break

        # Query the API to get the next pick up dates
        response = requests.get(f'Https://www.goldcoast.qld.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={siteId}&ocsvclang=en-AU')
        data = json.loads(response.text)

        # The above only gives us partial HTML code, this fixes that so we can easily search for the dates
        html = BeautifulSoup(data["responseContent"], features="lxml")

        # Search through the returned HTML for the dates
        waste = html.body.find('div', attrs={'class':'general-waste'}).find('div', attrs={'class':'next-service'}).text.strip()
        recycling = html.body.find('div', attrs={'class':'recycling'}).find('div', attrs={'class':'next-service'}).text.strip()
        green = html.body.find('div', attrs={'class':'green-waste'}).find('div', attrs={'class':'next-service'}).text.strip()

        # Convert the dates to what is expected
        waste_collectiondate = date.fromisoformat(datetime.strptime(waste, '%a %d/%m/%Y').strftime('%Y-%m-%d'))
        recycling_collectiondate = date.fromisoformat(datetime.strptime(recycling, '%a %d/%m/%Y').strftime('%Y-%m-%d'))
        green_collectiondate = date.fromisoformat(datetime.strptime(green, '%a %d/%m/%Y').strftime('%Y-%m-%d'))

        entries = []

        # Every collection day includes rubbish
        entries.append(
            Collection(
                date = waste_collectiondate, # Collection date
                t = "Rubbish",
                icon=ICON_MAP.get("DOMESTIC")
            )
        )

        # Check to see if it's recycling week
        if (recycling_collectiondate - today).days >= 0:
            entries.append(
                Collection(
                    date=recycling_collectiondate,
                    t="Recycling",
                    icon=ICON_MAP.get("RECYCLE")
                )
            )

        # Check to see if it's green waste week
        if (green_collectiondate - today).days >= 0:
            entries.append(
                Collection(
                    date=green_collectiondate,
                    t="Garden",
                    icon=ICON_MAP.get("ORGANIC")
                )
            )

        # Return our result
        return entries
