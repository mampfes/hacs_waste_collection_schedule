from datetime import datetime
from urllib.parse import quote as urlquote

import requests
from waste_collection_schedule import Collection

TITLE = "Tewkesbury Borough Council Waste and Recycling"
DESCRIPTION = "Home waste collection schedule for Tewkesbury Borough Council"
URL = "https://www.tewkesbury.gov.uk/waste-and-recycling"
TEST_CASES = {
    "Council Office": {"postcode": "GL20 5TT"},
    "Council Office No Spaces": {"postcode": "GL205TT"},
}

API_URL = "https://api-2.tewkesbury.gov.uk/general/rounds/%s/nextCollection"

ICONS = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Food": "mdi:silverware-fork-knife",
}


class Source:
    def __init__(self, postcode: str = None):
        self._postcode = postcode

    def fetch(self):
        if self._postcode is None:
            raise Exception("postcode not set")

        encoded_postcode = urlquote(self._postcode)
        request_url = API_URL % encoded_postcode
        response = requests.get(request_url)

        response.raise_for_status()
        data = response.json()

        entries = []

        if data["status"] == "OK":
            schedule = data["body"]
            for schedule_entry in schedule:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            schedule_entry["NextCollection"], "%Y-%m-%d").date(),
                        t=schedule_entry["collectionType"],
                        icon=ICONS.get(schedule_entry["collectionType"])
                    )
                )

        return entries
