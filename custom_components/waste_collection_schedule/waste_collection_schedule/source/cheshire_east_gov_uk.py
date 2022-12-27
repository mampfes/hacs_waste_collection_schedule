from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Cheshire East Council"
DESCRIPTION = "Source for cheshireeast.gov.uk services for Cheshire East"
URL = "https://cheshireeast.gov.uk"
TEST_CASES = {
    "houseUPRN": {"uprn": "100010132071"},
    "houseAddress": {"postcode": "WA16 0AY", "name_number": "1"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Mixed Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}


class Source:
    def __init__(self, uprn=None, postcode=None, name_number=None):
        self._uprn = uprn
        self._postcode = postcode
        self._name_number = name_number

    def fetch(self):
        session = requests.Session()

        if self._postcode and self._name_number:
            # Lookup postcode and number to get UPRN
            params = {
                "postcode": self._postcode,
                "propertyname": self._name_number,
            }
            r = session.get(
                "https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/Search",
                params=params,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, features="html.parser")
            s = soup.find("a", attrs={"class": "get-job-details"})

            if s is None:
                raise Exception("address not found")
            self._uprn = s["data-uprn"]

        if self._uprn is None:
            raise Exception("uprn not set")

        params = {"uprn": self._uprn}
        r = session.get(
            "https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/GetBartecJobList",
            params=params,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        s = soup.find_all("td", attrs={"class": "visible-cell"})

        entries = []

        for cell in s:
            labels = cell.find_all("label")
            if labels:
                date = datetime.strptime(labels[1].text, "%d/%m/%Y").date()
                type = labels[2].text.removeprefix("Empty Standard ")
                entries.append(
                    Collection(
                        date=date,
                        t=type,
                        icon=ICON_MAP.get(type),
                    )
                )

        return entries
