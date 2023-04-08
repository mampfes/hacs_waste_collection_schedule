from datetime import datetime
import requests
import json
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Müllabfuhr Deutschland"
DESCRIPTION = "Source for Müllabfuhr, Germany"
URL = "https://portal.muellabfuhr-deutschland.de/"
TEST_CASES = {
    "TestcaseI": {
        "client": "Landkreis Hildburghausen",
        "city": "Gompertshausen",
    },
}

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "gelbe Tonne/Leichtverpackungen": "mdi:recycle",
    "Papier":"mdi:package-variant",
    "Biomüll": "mdi:leaf",
}


class Source:
    def __init__(self, client, city):
        self._client = client
        self._city = city

    def fetch(self):

        #get Client
        url = URL + "/api-portal/mandators"

        r = requests.get(url)
        r.raise_for_status()
        clients = r.json()

        for client in clients:
          if self._client == client["name"]:
            clientid = client["id"]

        if not clientid:
          raise Exception("Sorry, no client found")

        #get client config
        url = URL + "api-portal/mandators/" + clientid + "/config"
        r = requests.get(url)
        r.raise_for_status()
        config = r.json()

        configid = config["calendarRootLocationId"]

        #get city list
        url = URL + "api-portal/mandators/" + clientid + "/cal/location/" + configid + "?includeChildren=true"
        r = requests.get(url)
        r.raise_for_status()
        cities = r.json()

        for city in cities["children"]:
          if self._city == city["name"]:
            cityid = city["id"]

        if not cityid:
          raise Exception("Sorry, no city found")

        #get pickups
        url = URL + "/api-portal/mandators/" + clientid + "/cal/location/" + cityid + "/pickups"
        r = requests.get(url)
        r.raise_for_status()
        pickups = r.json()

        entries = []
        for pickup in pickups:
          d = datetime.strptime(pickup["date"], "%Y-%m-%d").date()
          entries.append(
            Collection(d, pickup["fraction"]["name"], icon=ICON_MAP.get(pickup["fraction"]["name"]))
          )

        return entries
