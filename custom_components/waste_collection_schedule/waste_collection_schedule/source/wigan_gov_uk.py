# Credit where it's due:
# This is predominantly a refactoring of the Wigan Borough Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wigan Council"
DESCRIPTION = "Source for wigan.gov.uk services for Wigan Council, UK."
URL = "https://wigan.gov.uk"

TEST_CASES = {
    "Test_001": {"postcode": "WN5 9BH", "uprn": "100011821616"},
    "Test_002": {"postcode": "WN6 8RG", "uprn": "100011776859"},
    "Test_003": {"postcode": "wn36au", "uprn": 100011749007},
}

ICON_MAP = {
    "BLACK BIN": "mdi:trash-can",
    "BROWN BIN": "mdi:glass-fragile",
    "GREEN BIN": "mdi:leaf",
    "BLUE BIN": "mdi:recycle",
}

REGEX_ORDINALS = r"(st|nd|rd|th)"


class Source:
    def __init__(self, postcode, uprn):
        self._postcode = str(postcode.upper())
        self._uprn = str(uprn).zfill(12)

    def get_asp_var(self, broth, id) -> str:
        asp_var = broth.find("input", {"id": id}).get("value")
        return asp_var

    def fetch(self):

        # Initiate a session to generate required ASP variables
        s = requests.Session()
        r0 = s.get("https://apps.wigan.gov.uk/MyNeighbourhood/")
        r0.raise_for_status()
        soup = BeautifulSoup(r0.text, "html.parser")

        # Build initial search payload
        payload = {
            "__VIEWSTATE": self.get_asp_var(soup, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": self.get_asp_var(soup, "__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": self.get_asp_var(soup, "__EVENTVALIDATION"),
            "ctl00$ContentPlaceHolder1$txtPostcode": self._postcode,
            "ctl00$ContentPlaceHolder1$btnPostcodeSearch": "Search",
        }

        # Get address list
        r1 = s.post("https://apps.wigan.gov.uk/MyNeighbourhood/", payload)
        r1.raise_for_status()
        soup = BeautifulSoup(r1.text, features="html.parser")

        # Build address-specific payload
        payload = {
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$lstAddresses",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": self.get_asp_var(soup, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": self.get_asp_var(soup, "__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": self.get_asp_var(soup, "__EVENTVALIDATION"),
            "ctl00$ContentPlaceHolder1$txtPostcode": self._postcode,
            "ctl00$ContentPlaceHolder1$lstAddresses": "UPRN" + self._uprn,
        }

        # Get the collection schedule page
        r2 = s.post("https://apps.wigan.gov.uk/MyNeighbourhood/", payload)
        r2.raise_for_status()
        soup = BeautifulSoup(r2.text, features="html.parser")

        # Extract the collection schedules
        bin_collections = soup.findAll("div", {"class": "BinsRecycling"})
        entries = []
        for bin in bin_collections:
            waste_type = bin.find("h2").text
            waste_date = bin.find("div", {"class": "dateWrapper-next"}).get_text(
                strip=True
            )
            waste_date = re.compile(REGEX_ORDINALS).sub("", waste_date.split("day")[1])
            waste_date = datetime.strptime(waste_date, "%d%b%Y").date()
            entries.append(
                Collection(
                    date=waste_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.upper()),
                )
            )

        return entries
