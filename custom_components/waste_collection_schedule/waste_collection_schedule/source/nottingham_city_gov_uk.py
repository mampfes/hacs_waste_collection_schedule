import json
import datetime
import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "nottinghamcity.gov.uk"
DESCRIPTION = "Source for nottinghamcity.gov.uk services for the city of Nottingham, UK."
URL = "https://nottinghamcity.gov.uk"
TEST_CASES = {
    "Douglas Rd, Nottingham NG7 1NW": {"uprn": "100031540175"},
    "Harlaxton Drive, Nottingham, NG7 1JE": {"uprn": "100031553830"},
}

BINS = {
    "DryRecyclingDay": {
        "icon": "mdi:recycle",
        "name": "Recycling"
    },
    "DomesticDay": {
        "icon": "mdi:trash-can",
        "name": "General"
    },
    "GardenDay": {
        "icon": "mdi:leaf",
        "name": "Garden"
    },
    "FoodWaste": {
        "icon": "mdi:food-apple",
        "name": "Food"
    }
}

class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        # get json file
        r = requests.get(
            f"https://geoserver.nottinghamcity.gov.uk/myproperty/handler/proxy.ashx?http://geoserver.nottinghamcity.gov.uk/wcf/BinCollection.svc/livebin/{self._uprn}"
        )

        # extract data from json
        data = json.loads(r.text)

        entries = []

        today = datetime.date.today()

        for bin in BINS.keys():
            props = BINS[bin]
            day = data["CollectionDetails"][bin]
            if day == "Not Applicable":
                continue

            day = time.strptime(day, "%A").tm_wday

            # RecyclingWeek being B means recycling is on even numbered weeks
            week_offset = 0
            recycling_shift = data["CollectionDetails"]["RecyclingWeek"] == "A"
            domestic_shift = data["CollectionDetails"]["RecyclingWeek"] == "B"

            if bin == "DryRecyclingDay":
                week_offset = (datetime.date.today().isocalendar().week + recycling_shift) % 2
            elif bin == "DomesticDay":
                week_offset = (datetime.date.today().isocalendar().week + domestic_shift) % 2

            next_date = today + datetime.timedelta(days=day, weeks=week_offset)

            entries.append(
               Collection(
                   date = next_date,
                   t = props["name"],
                   icon = props["icon"]
               )
            )

        return entries
