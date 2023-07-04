from datetime import datetime
from waste_collection_schedule import Collection

import requests

TITLE = "Australian Capital Territory (ACT)"
DESCRIPTION = "Source script for Australian Capital Territory (ACT)."
URL = "https://www.cityservices.act.gov.au/recycling-and-waste"
TEST_CASES = {
    "Bruce": {"suburb": "Bruce"},
    "Amaroo": {"suburb": "amaroo"},
    "Charnwood": {"suburb": "CHARNWOOD"}
}

API_URL = "https://www.data.act.gov.au/resource/jzzy-44un.json"
ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycle": "mdi:recycle",
    "Organic": "mdi:leaf",
}


class Source:
    def __init__(self, suburb):  # argX correspond to the args dict in the source configuration
        self.suburb = suburb

    def fetch(self):

        suburb = self.suburb.upper()

        r=requests.get(API_URL, params={"suburb": suburb})
        data = r.json()[0]

        entries = []  # List that holds collection schedule

        entries.append(
            Collection(
                date = datetime.strptime(data["garbage_pickup_date"], "%d/%m/%Y").date(),  # Collection date
                t = "Garbage",  # Collection type
                icon = "mdi:trash-can",  # Collection icon
            )
        )

        entries.append(
            Collection(
                date = datetime.strptime(data["recycling_pickup_date"], "%d/%m/%Y").date(),  # Collection date
                t = "Recycle",  # Collection type
                icon = "mdi:recycle",  # Collection icon
            )
        )

        entries.append(
            Collection(
                date = datetime.strptime(data["next_greenwaste_date"], "%d/%m/%Y").date(),  # Collection date
                t = "Organic",  # Collection type
                icon = "mdi:leaf",  # Collection icon
            )
        )

        return entries