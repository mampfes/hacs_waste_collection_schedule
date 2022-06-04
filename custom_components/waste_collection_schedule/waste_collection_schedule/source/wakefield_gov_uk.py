import logging

from datetime import datetime
from bs4 import BeautifulSoup

import requests
from waste_collection_schedule import Collection

TITLE = "wakefield.gov.uk"
DESCRIPTION = (
    "Source for wakefield.gov.uk services for Wakefield"
)
URL = "wakefield.gov.uk"
TEST_CASES = {
    "houseUPRN" : {"uprn": "63161064"},
}

API_URLS = {
    "collection": "https://www.wakefield.gov.uk/site/Where-I-Live-Results?uprn={}",
}

ICONS = {
    "Household waste": "mdi:trash-can",
    "Mixed recycling": "mdi:recycle",
    "Garden waste recycling": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None, postcode=None):
        self._uprn = uprn

    def fetch(self):
        user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"
        headers = {"User-Agent": user_agent}

        responseContent=None
        r = requests.get(f"https://www.wakefield.gov.uk/site/Where-I-Live-Results?uprn={self._uprn}", headers)
        responseContent = r.text
        
        soup = BeautifulSoup(responseContent, features="html.parser")
        entries = []
        
        #Full Credit to Rob Bradley for this: https://github.com/robbrad/UKBinCollectionData/blob/master/outputs/WakefieldCityCouncil.json

        for bins in soup.findAll(
            "div", {"class": lambda L: L and L.startswith("mb10 ind-waste-")}
        ):

            # Get the type of bin
            bin_types = bins.find_all("div", {"class": "mb10"})
            bin_type = bin_types[0].get_text(strip=True)

            # Find the collection dates
            binCollections = bins.find_all(
                "div", {"class": lambda L: L and L.startswith("col-sm-4")}
            )

            if binCollections:
                lastCollections = binCollections[0].find_all("div")
                nextCollections = binCollections[1].find_all("div")

                # Get the collection date
                lastCollection = lastCollections[1].get_text(strip=True)
                nextCollection = nextCollections[1].get_text(strip=True)

                if lastCollection:
                    entries.append(
                        Collection(
                            date=datetime.strptime(
                                nextCollection, "%d/%m/%Y"
                            ).date(),
                            t=bin_type,
                            icon=ICONS.get(bin_type)
                        )
                    )
           
        return entries


