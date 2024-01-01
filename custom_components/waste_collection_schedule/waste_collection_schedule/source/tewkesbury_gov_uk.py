from datetime import datetime
from urllib.parse import quote as urlquote

import requests
from waste_collection_schedule import Collection

TITLE = "Tewkesbury Borough Council"
DESCRIPTION = "Home waste collection schedule for Tewkesbury Borough Council"
URL = "https://www.tewkesbury.gov.uk"
TEST_CASES = {
    "UPRN example": {"uprn": 100120544973},
}

API_URL = "https://api-2.tewkesbury.gov.uk/incab/rounds/%s/next-collection"

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Food": "mdi:silverware-fork-knife",
}


class Source:
    def __init__(self, uprn: str = None):
        self.urpn = str(uprn)

    def fetch(self):
        if self.urpn is None:
            raise Exception("UPRN not set")

        encoded_urpn = urlquote(self.urpn)
        request_url = API_URL % encoded_urpn
        response = requests.get(request_url)

        response.raise_for_status()
        data = response.json()

        entries = []

        if data["status"] != "OK":
            raise Exception(f"Error fetching data. \"{data['status']}\": \n {data['body']}")
        
        schedule = data["body"]
        for schedule_entry in schedule:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        schedule_entry["NextCollection"], "%Y-%m-%d").date(),
                    t=schedule_entry["collectionType"],
                    icon=ICON_MAP.get(schedule_entry["collectionType"])
                )
            )
            

        return entries
