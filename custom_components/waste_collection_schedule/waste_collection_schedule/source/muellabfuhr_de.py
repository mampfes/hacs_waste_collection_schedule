from datetime import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Müllabfuhr Deutschland"
DESCRIPTION = "Source for Müllabfuhr, Germany"
URL = "https://portal.muellabfuhr-deutschland.de/"
TEST_CASES = {
    "TestcaseI": {
        "client": "Landkreis Hildburghausen",
        "city": "Gompertshausen",
    },
    "TestcaseII": {
        "client": "Saalekreis",
        "city": "Kabelsketal",
        "district": "Großkugel",
        "street": "Am Markt",
    },
    "TestcaseIII": {
        "client": "Saalekreis",
        "city": "Kabelsketal",
        "district": "Kleinkugel",
    },
}

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "gelbe Tonne/Leichtverpackungen": "mdi:recycle",
    "Papier":"mdi:package-variant",
    "Biomüll": "mdi:leaf",
}

class Source:
    def __init__(self, client, city, district = None, street = None):
        self._client = client
        self._city = city
        self._district = district
        self._street = street

    def fetch(self):
        clientid = None
        configid = None
        cityid = None
        districtid = None
        streetid = None
        cisFinal = False
        disFinal = False

        #get Client
        url = URL + "/api-portal/mandators"
        r = requests.get(url)
        r.raise_for_status()
        clients = r.json()

        for client in clients:
          if self._client == client["name"]:
            clientid = client["id"]

        if clientid is None:
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
            cisFinal = city["isFinal"]

        if cityid is None:
          raise Exception("Sorry, no city found")

        #get district list(optional)
        if self._district is not None and cisFinal == False:
          url = URL + "api-portal/mandators/" + clientid + "/cal/location/" + cityid + "?includeChildren=true"
          r = requests.get(url)
          r.raise_for_status()
          districts = r.json()

          for district in districts["children"]:
            if self._district == district["name"]:
              districtid = district["id"]
              disFinal = district["isFinal"]

          if districtid is None:
            raise Exception("Sorry, no district found")

        else:
          districtid = cityid

        #get street list(optional)
        if self._street is not None and disFinal == False:
          url = URL + "api-portal/mandators/" + clientid + "/cal/location/" + districtid + "?includeChildren=true"
          r = requests.get(url)
          r.raise_for_status()
          streets = r.json()

          for street in streets["children"]:
            if self._street == street["name"]:
              streetid = street["id"]

          if streetid is None:
            raise Exception("Sorry, no street found")

        else:
          streetid = districtid

        #get pickups
        url = URL + "/api-portal/mandators/" + clientid + "/cal/location/" + streetid + "/pickups"
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
