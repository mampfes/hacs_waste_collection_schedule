from datetime import datetime
from urllib.parse import quote as urlquote

import requests
from waste_collection_schedule import Collection

TITLE = "Tewkesbury Borough Council"
DESCRIPTION = "Home waste collection schedule for Tewkesbury Borough Council"
URL = "https://www.tewkesbury.gov.uk"
TEST_CASES = {
    "Council Office": {"postcode": "GL20 5TT"},
    "Council Office No Spaces": {"postcode": "GL205TT"},
    "UPRN example": {"uprn": 100120544973},
}

API_URL = "https://api-2.tewkesbury.gov.uk/general/rounds/%s/nextCollection"

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Food": "mdi:silverware-fork-knife",
}


class Source:
    def __init__(self, postcode: str = None, uprn: str = None):
        self._post_or_uprn = str(uprn) if uprn else postcode

    def fetch(self):
        if self._post_or_uprn is None:
            raise Exception("postcode not set")

        encoded_postcode = urlquote(self._post_or_uprn)
        request_url = API_URL % encoded_postcode
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
