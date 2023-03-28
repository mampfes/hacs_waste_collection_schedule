from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "London Borough of Merton"

DESCRIPTION = "Source for www.merton.gov.uk services for London Borough of Merton, UK"

URL = "https://www.merton.gov.uk/"

TEST_CASES = {
    "test 1": {"property": "28186366"},
    "test 2": {"property": "28166100"},
}

API_URL = "https://myneighbourhood.merton.gov.uk/Wasteservices/WasteServices.aspx"


ICON_MAP = {
    "Food waste": "mdi:food",
    "Paper and card": "mdi:newspaper",
    "Plastics, glass, cans and cartons": "mdi:glass-fragile",
    "Rubbish": "mdi:trash-can",
    "Textiles": "mdi:hanger",
    "Household batteries": "mdi:battery",
}


class Source:
    def __init__(self, property: str):
        self._property = property

    def fetch(self):
        entries = []
        session = requests.Session()
        params = {"ID": self._property}
        r = session.get(API_URL, params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        soup.prettify()

        # Search for the specific bin in the table using BS4
        collections = soup.find("table", class_=("collectiondays")).find_all(
            "tr",
            class_=(
                "food-caddy",
                "papercard-wheelie",
                "plastics-boxes",
                "rubbish-wheelie",
                "textiles",
                "batteries",
            ),
        )
        if not collections:
            raise Exception("No collections found for given UPRN")
        # Loop the collections
        for collection in collections:
            # Get all the cells
            cells = collection.find_all("td")
            # First cell is the bin_type
            title = cells[0].get_text().strip()
            # Date is on the second cell, second paragraph, wrapped in p
            collectionDate = cells[1].select("p > b")[2].get_text(strip=True)
            # Add data to the main JSON Wrapper
            entries.append(
                Collection(
                    date=datetime.strptime(collectionDate, "%d %B %Y").date(),
                    t=title,
                    icon=ICON_MAP.get(title),
                )
            )
        return entries
