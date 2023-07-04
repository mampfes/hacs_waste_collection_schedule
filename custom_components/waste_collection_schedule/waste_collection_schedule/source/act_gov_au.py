from datetime import datetime
from waste_collection_schedule import Collection

import requests

TITLE = "Australian Capital Territory (ACT)"
DESCRIPTION = "Source script for Australian Capital Territory (ACT)."
URL = "https://www.cityservices.act.gov.au/recycling-and-waste"
TEST_CASES = {
    "Bruce": {"suburb": "Bruce"},
    "Amaroo": {"suburb": "amaroo"},
    "Charnwood Thursday": {"suburb": "CHARNWOOD", "split_suburb": "Thursday"},
    "Charnwood Tuesday": {"suburb": "CHARNWOOD", "split_suburb": "Tuesday"},
    "Dunlop North": {"suburb": "DUNLOP", "split_suburb": "NORTH"},
    "Dunlop South": {"suburb": "DUNLOP", "split_suburb": "south"}
}

API_URL = "https://www.data.act.gov.au/resource/jzzy-44un.json"
ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycle": "mdi:recycle",
    "Organic": "mdi:leaf",
}


class Source:
    def __init__(self, suburb, split_suburb = ""):  # argX correspond to the args dict in the source configuration
        self.suburb = suburb
        self.split_suburb = split_suburb

    def fetch(self):

        suburb = self.suburb.upper()
        split_suburb = self.split_suburb.capitalize()

        if split_suburb != "":
            r=requests.get(API_URL, params={"suburb": suburb, "split_suburb": split_suburb})
        else:
            r=requests.get(API_URL, params={"suburb": suburb})
        
        if len(r.json()) == 0:
            return []

        data = r.json()[0]

        entries = []  # List that holds collection schedule

        entries.append(
            Collection(
                date = datetime.strptime(data["garbage_pickup_date"], "%d/%m/%Y").date(),  # Collection date
                t = "Garbage",  # Collection type
                icon = ICON_MAP["Garbage"],  # Collection icon
            )
        )

        entries.append(
            Collection(
                date = datetime.strptime(data["recycling_pickup_date"], "%d/%m/%Y").date(),  # Collection date
                t = "Recycle",  # Collection type
                icon = ICON_MAP["Recycle"],  # Collection icon
            )
        )

        entries.append(
            Collection(
                date = datetime.strptime(data["next_greenwaste_date"], "%d/%m/%Y").date(),  # Collection date
                t = "Organic",  # Collection type
                icon = ICON_MAP["Organic"],  # Collection icon
            )
        )

        return entries