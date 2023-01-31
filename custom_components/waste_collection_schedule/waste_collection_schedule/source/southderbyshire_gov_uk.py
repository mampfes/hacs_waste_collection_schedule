import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "South Derbyshire District Council"
DESCRIPTION = (
    "Source for www.southderbyshire.gov.uk services for South Derbyshire "
)
URL = "https://www.southderbyshire.gov.uk/"
TEST_CASES = {
    "test case 1": {"uprn": "100030233745"},
    "test case 2": {"uprn": "10090304958"},
}

API_URL = "https://maps.southderbyshire.gov.uk/iShareLIVE.web/getdata.aspx?RequestType=LocalInfo&ms=mapsources/MyHouse&format=JSON&group=Recycling%20Bins%20and%20Waste|Next%20Bin%20Collections&uid="

ICON_MAP = {
    "Black": "mdi:trash-can",
    "Green": "mdi:recycle",
    "Brown": "mdi:leaf",
    "Podback": "mdi:coffee",
}

class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def _extract_date(self, text):
        # find date and return
        date = re.search(r'(\d{2} \w+ \d{4})', text).group(1)
        date = datetime.strptime(date, '%d %B %Y').date()
        return date

    def fetch(self):
        entries = []

        session = requests.Session()

        r = session.get(f"{API_URL}{self._uprn}")
        soup = BeautifulSoup(r.json()['Results']['Next_Bin_Collections']['_'], features="html.parser")
        collections = soup.find_all("div", recursive=False)

        if not collections:
            raise Exception("No collections found for given UPRN")

        for collection in collections:
            bintypes = re.findall(r'Green|Brown|Black|Podback', collection.find("img")["alt"])

            for bintype in bintypes:
                entries.append(
                    Collection(
                        date=self._extract_date(collection.text),
                        t=bintype if bintype == "Podback" else bintype + " bin",
                        icon=ICON_MAP.get(bintype),
                    )
                )

        return entries