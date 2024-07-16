import json
import urllib.parse
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Uppsala Vatten och Avfall AB"
DESCRIPTION = "Source script for uppsalavatten.se"
URL = "https://www.uppsalavatten.se"

TEST_CASES = {
    "Test1": {
        "city": "BJÖRKLINGE",
        "street": "SADELVÄGEN 1",
    },
    "Test2": {
        "city": "BJÖRKLINGE",
        "street": "BJÖRKLINGE-GRÄNBY 33",
    },
    "Test3": {
        "city": "BJÖRKLINGE",
        "street": "BJÖRKLINGE-GRÄNBY 20",
    },
}

API_URLS = {
    "address_search": "https://futureweb.uppsalavatten.se/Uppsala/FutureWebBasic/SimpleWastePickup/SearchAdress",
    "collection": "https://futureweb.uppsalavatten.se/Uppsala/FutureWebBasic/SimpleWastePickup/GetWastePickupSchedule",
}


ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:food-apple",
    "Slam": "",
}

MONTH_MAP = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "Maj": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Okt": 10,
    "Nov": 11,
    "Dec": 12,
}


class Source:
    def __init__(self, street, city):
        self.street = street
        self.city = city
        # self.facid = facid

    def fetch(self):
        # request to get facility id
        addresslist = requests.post(
            API_URLS["address_search"],
            {"searchText": f"{self.street.upper()}, {self.city.upper()}"},
        )
        addresslist.raise_for_status()
        adresslist_json = json.loads(addresslist.text)

        payload = {"address": adresslist_json["Buildings"][0]}

        payload_str = urllib.parse.urlencode(payload, encoding="utf8")
        # request for the wasteschedule
        wasteschedule = requests.get(API_URLS["collection"], params=payload_str)
        wasteschedule.raise_for_status()

        data = json.loads(wasteschedule.text)
        entries = []
        for i in data["RhServices"]:
            icon = ICON_MAP.get(i["WasteType"])
            if "v" in i["NextWastePickup"]:
                date_parts = i["NextWastePickup"].split()
                month = MONTH_MAP[date_parts[1]]
                date_joined = "-".join([date_parts[0], str(month), date_parts[2]])
                date = datetime.strptime(date_joined, "v%W-%m-%Y").date()
            elif not i["NextWastePickup"]:
                continue
            else:
                date = datetime.strptime(i["NextWastePickup"], "%Y-%m-%d").date()

            entries.append(
                Collection(
                    t=i["WasteType"],
                    icon=icon,
                    date=date,
                )
            )
        return entries
