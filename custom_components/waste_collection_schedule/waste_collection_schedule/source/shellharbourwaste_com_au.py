from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Shellharbour City Council"
DESCRIPTION = "Source script for shellharbourwaste.com.au"
URL = "https://shellharbourwaste.com.au"
COUNTRY = "au"
TEST_CASES = {"TestName1": {"zoneID": "Monday A"}, "TestName2": {"zoneID": "Friday A"}}

API_URL = "https://www.shellharbourwaste.com.au/waste-collection"

ICON_MAP = {
    "Waste": "mdi:trash-can",
    "FOGO": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


def findUrl(zoneID):
    # Take Zone ID and find url to parse
    r = requests.get(
        f"https://www.shellharbourwaste.com.au/wp-json/rb_co/v1/get-waste-url?zone={zoneID}"
    )
    r.raise_for_status
    d = r.json()
    return d["url"]


class Source:
    def __init__(self, zoneID):
        self._zoneID = zoneID

    def fetch(self):
        data = {"Referer": "https://www.shellharbourwaste.com.au/find-my-bin-day/"}
        pageurl = findUrl(self._zoneID)
        r = requests.get(f"{pageurl}", data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        collections = soup.select("div.waste-block__content")
        entries = []
        for entry in collections:
            waste_type = entry.find("h3", class_="waste-block__title").text
            date_string = entry.find("time", class_="waste-block__time").text.strip()
            pickupdate = datetime.strptime(date_string, "%d/%m/%Y")
            entries.append(
                Collection(
                    date=pickupdate.date(),
                    t=waste_type.split("/")[0],
                    icon=ICON_MAP.get(waste_type.split("/")[0]),
                )
            )
        return entries
