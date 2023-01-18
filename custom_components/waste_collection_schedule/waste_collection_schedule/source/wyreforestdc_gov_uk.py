import datetime
import logging

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Wyre Forest District Council"
DESCRIPTION = "Source for wyreforestdc.gov.uk, Wyre Forest District Council, UK"
URL = "https://www.wyreforestdc.gov.uk"

TEST_CASES = {
    "2 Kinver Avenue, Kidderminster": {"uprn": 100120731673},
    "14 Forestry Houses, Callow Hill": {"post_code": "DY14 9XQ", "number": 14},
    "The Park, Stourbridge": {"post_code": "DY9 0EX", "name": "The Park"},
}

API_URLS = {
    "address_search": "https://forms.wyreforestdc.gov.uk/bindays/",
    "collection": "https://forms.wyreforestdc.gov.uk/bindays/Home/Details",
}

ICON_MAP = {
    "rubbish (black bin)": "mdi:trash-can",
    "recycling (green bin)": "mdi:recycle",
    "garden waste (brown bin)": "mdi:leaf",
}

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._post_code = post_code
        self._number = number
        self._name = name
        self._uprn = uprn

    def fetch(self):
        s = requests.Session()

        if not self._uprn:
            # look up the UPRN for the address
            payload = {"searchTerm": self._post_code}
            r = s.post(str(API_URLS["address_search"]), data=payload)

            soup = BeautifulSoup(r.text, features="html.parser")
            propertyUprns = soup.find("select", {"id": "UPRN"}).findAll("option")
            for match in propertyUprns:
                if self._name:
                    if (
                        match.text.strip()
                        .capitalize()
                        .startswith(self._name.capitalize())
                    ):
                        self._uprn = match["value"]
                if self._number:
                    if match.text.strip().startswith(str(self._number)):
                        self._uprn = match["value"]

        # GET request returns schedule for matching uprn
        payload = {"UPRN": self._uprn}
        r = s.post(str(API_URLS["collection"]), data=payload)
        r.raise_for_status()

        entries = []

        # Extract waste types and dates from responseContent
        soup = BeautifulSoup(r.text, "html.parser")
        x = soup.findAll("p")
        for i in x:  # ignores elements containing address and marketing message
            if "this week is a " in i.text:
                for round_type in ICON_MAP:
                    if round_type in i.text:
                        dayRaw = i.find("strong")
                        dayName = dayRaw.contents[0].strip()
                        d = datetime.date.today()
                        nextDate = d + datetime.timedelta(
                            (DAYS.index(dayName) + 1 - d.isoweekday()) % 7
                        )
                        entries.append(
                            Collection(
                                date=nextDate,
                                t=round_type,
                                icon=ICON_MAP.get(round_type),
                            )
                        )

        return entries
