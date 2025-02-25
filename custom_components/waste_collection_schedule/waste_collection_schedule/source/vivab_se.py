import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentNotFound,
    SourceArgumentSuggestionsExceptionBase,
)

TITLE = "VIVAB Sophämtning"
DESCRIPTION = "Source for VIVAB waste collection."
URL = "https://www.vivab.se"
TEST_CASES = {
    "Varberg: Gallerian": {"street_address": "Västra Vallgatan 2, Varberg"},
    "Varberg: Polisen": {"street_address": "Östra Långgatan 5, Varberg"},
    "Falkenberg: Storgatan 1": {"street_address": "Storgatan 1, FALKENBERG"},
    "Falkenberg: Östergränd 4": {"street_address": "Östergränd 4, Falkenberg"},
    "Storgtan 26, Falkenberg": {"street_address": "Storgatan 26, Falkenberg"},
    "Storgtan 26, Falkenberg 1": {
        "street_address": "Falkenberg",
        "building_id": "0012165858",
    },
    "Storgtan 26, Falkenberg  2": {
        "street_address": "Falkenberg",
        "building_id": "9593062021",
    },
}

API_URLS = {
    "falkenberg": "https://minasidor.vivab.info/FutureWebFalken/SimpleWastePickup/",
    "varberg": "https://minasidor.vivab.info/FutureWebVarberg/SimpleWastePickup/",
}


class Source:
    def __init__(self, street_address: str, building_id: str | int | None = None):
        if not street_address:
            raise SourceArgumentException(
                "street_address",
                "Street address must be provided and must either be a valid address or 'Varberg' or 'Falkenberg' if using with building_id",
            )

        self._building_id = building_id
        self._street_address = street_address
        region = None
        if "falkenberg" in street_address.lower():
            region = "falkenberg"
        elif "varberg" in street_address.lower():
            region = "varberg"
        if region is None:
            if self._building_id:
                raise SourceArgumentSuggestionsExceptionBase(
                    "street_address",
                    "street_address should be 'Varberg' or 'Falkenberg' if using with building_id",
                    ["Varberg", "Falkenberg"],
                )
            raise SourceArgumentException(
                "street_address",
                "Address not supported should end with ', Varberg' or ', Falkenberg'",
            )
        self._api_url = API_URLS[region]

    def _fetch_building_id(self) -> None:
        search_data = {"searchText": self._street_address.split(",")[0].strip()}

        response = requests.post(
            f"{self._api_url}SearchAdress",
            data=search_data,
        )

        building_data = json.loads(response.text)
        if not (
            building_data
            and "Succeeded" in building_data
            and "Buildings" in building_data
            and len(building_data["Buildings"]) > 0
        ):
            raise SourceArgumentNotFound("street_address", self._street_address)

        self._building_id = None

        if len(building_data["Buildings"]) == 1:
            # support only first building match
            building_id_matches = re.findall(
                r"\(([0-9]+)\)", building_data["Buildings"][0]
            )
            if not building_id_matches or len(building_id_matches) == 0:
                raise ValueError("No building id found")
            self._building_id = building_id_matches[0]
            return

        building: str
        addresses = []
        perfect_matches = []
        for building in building_data["Buildings"]:
            address, building_id_match = building.split(" (")
            addresses.append(address)
            building_id_match.removesuffix(")")
            if address.lower().replace(" ", "").replace(
                ",", ""
            ) == self._street_address.lower().replace(" ", "").replace(",", ""):
                perfect_matches.append((address, building_id_match))

        if len(perfect_matches) == 1:
            self._building_id = perfect_matches[0][1]
            return
        if len(perfect_matches) > 1:
            raise ValueError(
                f"Multiple buildings found perfectly matching your search please use a building_id: {perfect_matches}"
            )

        raise SourceArgAmbiguousWithSuggestions(
            "street_address", self._street_address, addresses
        )

    def fetch(self):
        if not self._building_id:
            self._fetch_building_id()

        response = requests.get(
            f"{self._api_url}GetWastePickupSchedule",
            params={"address": f"({self._building_id})"},
        )

        waste_data = json.loads(response.text)
        if not ("RhServices" in waste_data and len(waste_data["RhServices"]) > 0):
            return []

        data = waste_data["RhServices"]

        entries = []
        for item in data:
            waste_type = item["WasteType"]
            icon = "mdi:trash-can"
            if waste_type == "Mat":
                icon = "mdi:food-apple"
            next_pickup = item["NextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
