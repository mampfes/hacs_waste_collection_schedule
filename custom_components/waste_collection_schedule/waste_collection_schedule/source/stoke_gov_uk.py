from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stoke-on-Trent"
DESCRIPTION = "Source for Stoke-on-Trent"
URL = "https://www.stoke.gov.uk/"

TEST_CASES = {
    "Test1": {"uprn": "3455011383"},
    "Test2": {"uprn": 3455011391},
}

ICON_MAP = {"ORG": "mdi:leaf", "RES": "mdi:trash-can", "REC": "mdi:recycle"}

API_URL = "https://www.stoke.gov.uk/jadu/custom/webserviceLookUps/BarTecWebServices_missed_bin_calendar.php?UPRN="

DATE_FORMAT = "%d/%m/%Y"  # format of the date string in the collection table


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        r = requests.get(API_URL + self._uprn)
        soup = BeautifulSoup(r.text, features="xml")

        # find all BinRound elements
        bin_rounds = soup.find_all("BinRound")

        entries = []

        for bin_round in bin_rounds:
            bin = bin_round.find("Bin").text
            bintype = "RES"
            if "REC" in bin.upper():
                bintype = "REC"
            if "ORG" in bin.upper():
                bintype = "ORG"
            if "RES" in bin.upper():
                bintype = "RES"

            # round_name = bin_round.find('RoundName').text
            date_time = bin_round.find("DateTime").text.split(" ")[0]

            date = datetime.strptime(date_time, DATE_FORMAT).date()
            entries.append(Collection(date=date, t=bin, icon=ICON_MAP.get(bintype)))

        return entries
