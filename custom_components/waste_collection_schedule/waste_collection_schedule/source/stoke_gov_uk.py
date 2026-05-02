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
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        }
        r = requests.get(API_URL + self._uprn, headers=headers)

        if r.status_code == 403 or "403 Client Error" in r.text:
            raise Exception("Rate limiting or IP ban may be in effect")

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
