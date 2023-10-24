import datetime
import json
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "The Hills Shire Council, Sydney"
DESCRIPTION = "Source for Hills Shire Council, Sydney, Australia waste collection."
URL = "https://www.thehills.nsw.gov.au/"
TEST_CASES = {
    "Annangrove, Amanda Place 10": {
        "suburb": "ANNANGROVE",
        "street": "Amanda Place",
        "houseNo": 10,
    },
    "Annangrove, Amanda Place 10": {
        "suburb": "ANn ANgROvE",
        "street": "amanda PlaC e",
        "houseNo": " 10 ",
    }
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, suburb, street, houseNo):
        self._suburb = suburb
        self._street = street
        self._houseNo = str(houseNo)
        self._url = "https://apps.thehills.nsw.gov.au/seamlessproxy/api"

    def fetch(self):
        # get list of suburbs
        r = requests.get(f"{self._url}/suburbs/get")
        data = json.loads(r.text)

        suburbs = {}
        for entry in data:
            suburbs[entry["Suburb"].strip().upper().replace(" ", "")] = entry["SuburbKey"]

        # check if suburb exists
        suburb_searh = self._suburb.strip().upper().replace(" ", "")
        if suburb_searh not in suburbs:
            raise Exception(f"suburb not found: {self._suburb}")
        suburbKey = suburbs[suburb_searh]

        # get list of streets for selected suburb
        r = requests.get(f"{self._url}/streets/{suburbKey}")
        data = json.loads(r.text)

        streets = {}
        for entry in data:
            streets[entry["Street"].strip().upper().replace(" ", "")] = entry["StreetKey"]

        # check if street exists
        street_search = self._street.strip().upper().replace(" ", "")
        if street_search not in streets:
            raise Exception(f"street not found: {self._street}")
        streetKey = streets[street_search]

        # get list of house numbers for selected street
        params = {"streetkey": streetKey, "suburbKey": suburbKey}
        r = requests.get(
            f"{self._url}/properties/GetPropertiesByStreetAndSuburbKey",
            params=params,
        )
        data = json.loads(r.text)

        houseNos = {}
        for entry in data:
            houseNos[
                (str(int(entry["HouseNo"])) + entry.get("HouseSuffix", "").strip()).strip().upper().replace(" ", "")
            ] = entry["PropertyKey"]

        # check if house number exists
        houseNo_search = self._houseNo.strip().upper().replace(" ", "")
        if houseNo_search not in houseNos:
            raise Exception(f"house number not found: {self._houseNo}")
        propertyKey = houseNos[houseNo_search]

        # get collection schedule
        r = requests.get(f"{self._url}/services/{propertyKey}")
        data = json.loads(r.text)

        entries = []
        for entry in data:
            name = entry["Name"]
            for dateStr in entry["CollectionDays"]:
                date = datetime.datetime.strptime(dateStr, "%Y-%m-%dT%H:%M:%S").date()
                entries.append(Collection(date, name))
        return entries
