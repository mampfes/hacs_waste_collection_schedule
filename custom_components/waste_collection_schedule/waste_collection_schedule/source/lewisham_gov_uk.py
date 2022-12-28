import datetime
import logging
import re

import requests
from waste_collection_schedule import Collection

TITLE = "London Borough of Lewisham"
DESCRIPTION = (
    "Source for services from the London Borough of Lewisham"
)
URL = "https://lewisham.gov.uk"
TEST_CASES = {
    "houseNumber": {"post_code": "SE41LR", "number": 4},
    "houseName": {"post_code": "SE233TE", "name": "The Haven"},
    "houseUprn": {"uprn": "10070495030"}
}

API_URLS = {
    "address_search": "https://lewisham.gov.uk/api/AddressFinder",
    "collection": "https://lewisham.gov.uk/api/roundsinformation",
}

URPN_DATA_ITEM = '{79b58e9a-0997-4f18-bb97-637fac570dd1}'

REGEX = "<strong>(?P<type>Food and garden waste|Recycling|Refuse).*?</strong>.*?>(?P<frequency>.*?)<.*?\\\\t(?P<weekday>[A-Za-z]*day).*?(?:<br><br>|[A-Za-z\\\\]*?(?P<next>\d{2}/\d{2}/\d{4}))"
DAYS =  ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"]

BINS = {
    "Refuse": {
        "icon": "mdi:trash-can",
        "alias": "Black Refuse"
        },
    "Recycling": {
        "icon": "mdi:recycle",
        "alias": "Green Recycling"
        },
    "Food": {
        "icon": "mdi:food-apple",
        "alias": "Grey Food"
        },
    "Garden": {
        "icon": "mdi:leaf",
        "alias": "Brown Garden"
        }
}

#_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._post_code = post_code
        self._number = number
        self._name = name
        self._uprn = uprn

    def fetch(self):
        now = datetime.date.today()
        if not self._uprn:
            
            # look up the UPRN for the address
            p = {'postcodeOrStreet': self._post_code}
            r = requests.post(API_URLS["address_search"], params=p)
            r.raise_for_status()
            addresses = r.json()

            if self._name:
                self._uprn = [
                    x["Uprn"] for x in addresses if (x["Title"]).upper().startswith(self._name.upper())
                ][0]
            elif self._number:
                self._uprn = [
                    x["Uprn"] for x in addresses if (x["Title"]).startswith(str(self._number))
                ][0]

            if not self._uprn:
                raise Exception(f"Could not find address {self._post_code} {self._number}{self._name}")

        p = {
            'item': URPN_DATA_ITEM,
            'uprn': self._uprn
            }
        r = requests.post(API_URLS["collection"], params=p)
        r.raise_for_status()
        
        entries = []

        response_pattern = re.compile(REGEX)
        collections = response_pattern.findall(r.text)

        for collection in collections:

            if collection[0].__contains__(' and '):
                collections.append([collection[0].split(" and ",2)[0].title().replace(" Waste",""), collection[1], collection[2], collection[3]])
                collections.append([collection[0].split(" and ",2)[1].title().replace(" Waste",""), collection[1], collection[2], collection[3]])
            else:
                if collection[3] != "":
                    nextDate = datetime.datetime.strptime(collection[3], "%d/%m/%Y").date()
                elif collection[1] == "WEEKLY":
                    d = datetime.date.today();
                    nextDate = d + datetime.timedelta((DAYS.index(collection[2].upper())+1 - d.isoweekday()) % 7)

                entries.append(
                    Collection(
                        date=nextDate,
                        t=BINS.get(collection[0])['alias'],
                        icon=BINS.get(collection[0])['icon']
                    )
                )

        return entries
