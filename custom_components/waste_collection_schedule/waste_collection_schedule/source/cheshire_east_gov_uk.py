import logging

from datetime import datetime
from bs4 import BeautifulSoup

import requests
from waste_collection_schedule import Collection

TITLE = "cheshireeast.gov.uk"
DESCRIPTION = (
    "Source for cheshireeast.gov.uk services for Cheshire East"
)
URL = "cheshireeast.gov.uk"
TEST_CASES = {
    "houseUPRN" : {"uprn": "100010090246"},
}

API_URLS = {
    "address_search": "https://servicelayer3c.azure-api.net/wastecalendar/address/search/",
    "collection": "https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/GetBartecJobList?uprn={}",
}

ICONS = {
    "GENERAL": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None):
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()
        
        r = session.get(f"https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/GetBartecJobList?uprn={self._uprn}")
        responseContent = r.text
        

        soup = BeautifulSoup(r.text, features="html.parser")
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
                        if "GENERAL" in label.text.upper():
                            type = "GENERAL"
                        if "RECYCLING" in label.text.upper():
                            type = "RECYCLING"
                        if "GARDEN" in label.text.upper():
                            type = "GARDEN"
                entries.append(
                Collection(
                     date = date,
                     t = type,
                     icon = ICONS.get(type),
                  )
                )
           
        return entries


