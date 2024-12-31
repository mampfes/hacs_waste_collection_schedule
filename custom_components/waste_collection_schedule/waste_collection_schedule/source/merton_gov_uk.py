from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Merton (Old)"
DESCRIPTION = "Source for www.merton.gov.uk services for London Borough of Merton, UK"
URL = "https://www.merton.gov.uk/"
TEST_CASES = {
    "Without Garden Waste": {"property": "25929128"},
    "With Garden Waste": {"property": "25937841"},
}
API_URL = "https://myneighbourhood.merton.gov.uk/Wasteservices/WasteServices.aspx"
WASTE_CLASSES: list = [
    "food-caddy",
    "papercard-wheelie",
    "plastics-boxes",
    "rubbish-wheelie",
    "textiles",
    "batteries",
    "garden",
]
ICON_MAP = {
    "Food waste": "mdi:food",
    "Paper and card": "mdi:newspaper",
    "Plastics, glass, cans and cartons": "mdi:glass-fragile",
    "Rubbish": "mdi:trash-can",
    "Textiles": "mdi:hanger",
    "Household batteries": "mdi:battery",
    "Garden waste": "mdi:leaf",
}


class Source:
    def __init__(self, property: str):
        self._property = property

    def fetch(self):
        session = requests.Session()

        params = {"ID": self._property}
        r = session.get(API_URL, params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # Search for table containing bin schedule info
        collections = soup.find("table", {"class": "collectiondays"})
        if not collections:
            raise Exception("No collections found for given property id")

        entries = []
        # iterate through waste types finding pick-up dates
        for item in WASTE_CLASSES:
            trs = collections.find("tr", {"class": item})
            cells = trs.find_all("td")
            # First cell is the bin_type
            title = cells[0].get_text().strip()
            # Date is in the second cell, second paragraph, wrapped in p
            # Not all properties have garden waste collections, so silently deal with the IndexError
            try:
                collectionDate = cells[1].select("p > b")[2].get_text(strip=True)
            except IndexError:
                pass
            else:
                try:
                    entries.append(
                        Collection(
                            date=datetime.strptime(
                                collectionDate, "%A %d %B %Y"
                            ).date(),
                            t=title,
                            icon=ICON_MAP.get(title),
                        )
                    )
                except ValueError:
                    entries.append(
                        Collection(
                            date=datetime.strptime(collectionDate, "%d %B %Y").date(),
                            t=title,
                            icon=ICON_MAP.get(title),
                        )
                    )

        return entries
