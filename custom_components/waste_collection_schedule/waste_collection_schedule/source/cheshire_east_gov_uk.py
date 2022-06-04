import logging

from datetime import datetime
from bs4 import BeautifulSoup

import requests
import urllib.parse
from waste_collection_schedule import Collection

TITLE = "cheshireeast.gov.uk"
DESCRIPTION = (
    "Source for cheshireeast.gov.uk services for Cheshire East"
)
URL = "cheshireeast.gov.uk"
TEST_CASES = {
    "houseUPRN" : {"uprn": "100010132071"},
    "houseAddress": {"postcode":"WA16 0AY", "name_number": "1"}
}

API_URLS = {
    "address_search": "https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/Search",
    "collection": "https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/GetBartecJobList?uprn={}",
}

ICONS = {
    "General Waste": "mdi:trash-can",
    "Mixed Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None, postcode=None, name_number=None):
        self._uprn = uprn
        self._postcode = postcode
        self.name_number = name_number

    def fetch(self):
        session = requests.Session()
        responseContent=None

        if(self._postcode and self.name_number):
            # Lookup postcode and number to get UPRN
            r = session.get(f"https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/Search?postcode={urllib.parse.quote(self._postcode.encode('utf8'))}&propertyname={self.name_number}")
            soup = BeautifulSoup(r.text, features="html.parser")
            s = soup.find("a", attrs={"class": "get-job-details"})
            self._uprn = s['data-uprn']

        if self._uprn:
            r = session.get(f"https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/GetBartecJobList?uprn={self._uprn}")
            responseContent = r.text
        
        soup = BeautifulSoup(responseContent, features="html.parser")
        s = soup.find_all("td", attrs={"class": "visible-cell"})

        entries = []

        for cell in s:
            labels = cell.find_all("label")
            date = None
            type = None
            if labels:
                for i,label in enumerate(labels):
                    if(i == 1):
                        date = datetime.strptime(label.text, "%d/%m/%Y")
                    if(i == 2):
                        for round_type in ICONS:
                            if round_type.upper() in label.text.upper():
                                type = round_type
                entries.append(
                Collection(
                     date = date.date(),
                     t = type,
                     icon = ICONS.get(type),
                  )
                )
           
        return entries


