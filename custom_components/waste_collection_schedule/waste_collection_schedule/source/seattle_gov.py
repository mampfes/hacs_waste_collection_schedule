import datetime
import json
import time
from urllib.parse import quote

import requests
from waste_collection_schedule import CollectionAppointment

TITLE = "Seattle Public Utilities"
DESCRIPTION = "Source for Seattle Public Utilities waste collection."
URL = "https://myutilities.seattle.gov/eportal/#/accountlookup/calendar"
TEST_CASES = {
    "City Hall": {"street_address": "600 4th Ave"},
    "Honey Hole": {"street_address": "703 E Pike St"},
    "Carmona Court": {"street_address": "1127 17th Ave E"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        start_time = int(time.time())

        # get json file
        r = requests.get(
            f"https://www.seattle.gov/UTIL/WARP/CollectionCalendar/GetCollectionDays?pApp=CC&pAddress={quote(self._street_address)}&start={start_time}"
        )

        # extract data from json
        data = json.loads(r.text)
        next_pickup = data[0]

        if not next_pickup["start"]:
            return []

        next_pickup_date = datetime.datetime.strptime(
            next_pickup["start"], "%a, %d %b %Y"
        ).date()

        # create entries for trash, recycling, and yard waste
        entries = []

        if next_pickup["Garbage"]:
            entries.append(
                CollectionAppointment(
                    date=next_pickup_date, t="Trash", icon="mdi:trash-can"
                )
            )
        if next_pickup["FoodAndYardWaste"]:
            entries.append(
                CollectionAppointment(
                    date=next_pickup_date, t="Food and Yard Waste", icon="mdi:leaf"
                )
            )
        if next_pickup["Recycling"]:
            entries.append(
                CollectionAppointment(
                    date=next_pickup_date, t="Recycling", icon="mdi:recycle"
                )
            )

        return entries
