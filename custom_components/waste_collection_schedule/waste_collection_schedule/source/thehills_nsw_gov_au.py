import datetime
import json
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "The Hills Shire Council, Sydney"
DESCRIPTION = "Source for Hills Shire Council, Sydney, Australia waste collection."
URL = "https://www.thehills.nsw.gov.au/"
TEST_CASES = {
    "Annangrove, Amanda Place 10": {
        "suburb": "ANNANGROVE",
        "street": "Amanda Place",
        "houseNo": 10,
    },
    "Annangrove, Amanda Place 10 (2)": {
        "suburb": "ANn ANgROvE",
        "street": "amanda PlaC e",
        "houseNo": " 10 ",
    },
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
            suburbs[entry["Suburb"].strip().upper().replace(" ", "")] = entry[
                "SuburbKey"
            ]

        # check if suburb exists
        suburb_search = self._suburb.strip().upper().replace(" ", "")
        if suburb_search not in suburbs:
            raise SourceArgumentNotFoundWithSuggestions(
                "suburb", self._suburb, suburbs.keys()
            )
        suburb_key = suburbs[suburb_search]

        # get list of streets for selected suburb
        r = requests.get(f"{self._url}/streets/{suburb_key}")
        data = json.loads(r.text)

        streets = {}
        for entry in data:
            streets[entry["Street"].strip().upper().replace(" ", "")] = entry[
                "StreetKey"
            ]

        # check if street exists
        street_search = self._street.strip().upper().replace(" ", "")
        if street_search not in streets:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, streets.keys()
            )
        street_key = streets[street_search]

        # get list of house numbers for selected street
        params = {"streetkey": street_key, "suburbKey": suburb_key}
        r = requests.get(
            f"{self._url}/properties/GetPropertiesByStreetAndSuburbKey",
            params=params,
        )
        data = json.loads(r.text)

        house_numbers = {}
        for entry in data:
            house_numbers[
                (str(int(entry["HouseNo"])) + entry.get("HouseSuffix", "").strip())
                .strip()
                .upper()
                .replace(" ", "")
            ] = entry["PropertyKey"]

        # check if house number exists
        houseNo_search = self._houseNo.strip().upper().replace(" ", "")
        if houseNo_search not in house_numbers:
            raise SourceArgumentNotFoundWithSuggestions(
                "houseNo", self._houseNo, house_numbers.keys()
            )
        property_key = house_numbers[houseNo_search]

        # get collection schedule
        r = requests.get(f"{self._url}/services/{property_key}")
        data = json.loads(r.text)

        entries = []
        for entry in data:
            name = entry["Name"]
            for dateStr in entry["CollectionDays"]:
                date = datetime.datetime.strptime(dateStr, "%Y-%m-%dT%H:%M:%S").date()
                entries.append(Collection(date, name))
        return entries
