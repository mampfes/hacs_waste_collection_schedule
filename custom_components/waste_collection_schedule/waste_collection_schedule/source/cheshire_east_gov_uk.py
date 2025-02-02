from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE = "Cheshire East Council"
DESCRIPTION = "Source for cheshireeast.gov.uk services for Cheshire East"
URL = "https://cheshireeast.gov.uk"
TEST_CASES = {
    "houseUPRN-VerifyTrue": {"uprn": "100010132073", "verify": True},
    "houseUPRN-VerifyFalse": {"uprn": "100010132073", "verify": False},
    "houseAddress-VerifyTrue": {"postcode": "WA16 0AY", "name_number": "3", "verify": True},
    "houseAddress-VerifyFalse": {"postcode": "WA16 0AY", "name_number": "3", "verify": False},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Mixed Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}


class Source:
    def __init__(self, uprn=None, postcode=None, name_number=None, verify=True):
        self._uprn = uprn
        self._postcode = postcode
        self._name_number = name_number
        self._verify = verify

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
                verify=self._verify,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, features="html.parser")
            s = soup.find("a", attrs={"class": "get-job-details"})

            if s is None or s["data-uprn"] is None:
                raise SourceArgumentExceptionMultiple(
                    ["postcode", "name_number"], "address not found"
                )
            self._uprn = s["data-uprn"]

        if self._uprn is None:
            raise SourceArgumentException(
                "uprn",
                "uprn not set but required if postcode and name_number are not set",
            )

        params = {"uprn": self._uprn}
        r = session.get(
            "https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax/GetBartecJobList",
            params=params,
            verify=self._verify,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        s = soup.find_all("td", attrs={"class": "visible-cell"})

        entries = []

        for cell in s:
            labels = cell.find_all("label")
            if labels:
                date = datetime.strptime(labels[1].text, "%d/%m/%Y").date()

                if "general waste" in labels[2].text.lower():
                    type = "General Waste"
                elif "mixed recycling" in labels[2].text.lower():
                    type = "Mixed Recycling"
                elif "garden waste" in labels[2].text.lower():
                    type = "Garden Waste"
                else:
                    type = "Unknown"

                entries.append(
                    Collection(
                        date=date,
                        t=type,
                        icon=ICON_MAP.get(type),
                    )
                )

        return entries
