from datetime import datetime
import json
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Boden Avfall och Återbruk"
DESCRIPTION = "Source for Boden Avfall och Återbruk waste collection."
URL = "https://www.boden.se"
TEST_CASES = {
    "Bodens Kommun": {"street_address": "KYRKGATAN 24, Boden"},
    "Gymnasiet": {"street_address": "IDROTTSGATAN 4 , BJÖRKNÄSGYMNASIET, Boden"},
}
COUNTRY = "se"
_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Brännbart": "mdi:trash-can",
    "Matavfall": "mdi:food",
    "Deponi": "mdi:recycle",
}

# This is based on the ssam_se source, just changed to work with boden.se
class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        params = {"searchText": self._street_address}
        # Use the street address to find the full street address with the building ID
        response = requests.post(
            "https://edpmobile.boden.se/FutureWeb/SimpleWastePickup/SearchAdress",
            params=params,
            timeout=30,
        )

        address_data = json.loads(response.text)
        address = None
        # Make sure the response is valid and contains data
        if address_data and len(address_data) > 0:
            # Check if the request was successful
            if address_data['Succeeded']:
                # The request can be successful but still not return any buildings at the specified address
                if len(address_data["Buildings"]) > 0:
                    address = address_data["Buildings"][0]
                else:
                    raise Exception(f"No returned building address for: {self._street_address}")
            else:
                raise Exception(f"The server failed to fetch the building data for: {self._street_address}")
        
        # Raise exception if all the above checks failed
        if not address:
            raise Exception(f"Failed to find building address for: {self._street_address}")

        # Use the address we got to get the waste collection schedule
        params = {"address": address}
        response = requests.get(
            "https://edpmobile.boden.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule",
            params=params,
            timeout=30,
        )

        data = json.loads(response.text)

        entries = []
        for item in data["RhServices"]:
            waste_type = ""
            next_pickup = item["NextWastePickup"]
            try:
                next_pickup_date = datetime.fromisoformat(next_pickup).date()
            except ValueError as _:
                # In some cases the date is just a month, so parse this as the
                # first of the month to atleast get something close
                try:
                    next_pickup_date = datetime.strptime(next_pickup, "%b %Y").date()
                except ValueError as month_parse_error:
                    _LOGGER.warning(
                        "Failed to parse date %s, %s,",
                        next_pickup,
                        str(month_parse_error),
                    )
                    continue

            waste_type_prefix = ""
            if item["WasteType"] in ["Brännbart", "Matavfall", "Deponi"]:
                waste_type_prefix = item["WasteType"] + ", "
            
            waste_type = (
                waste_type_prefix
                + item["BinType"]["ContainerType"]
                + " "
                + str(item["BinType"]["Size"])
                + item["BinType"]["Unit"]
            )
            # Get the icon for the waste type, default to help icon if not found
            icon = ICON_MAP.get(item["WasteType"], "mdi:help")

            found = found = any(x.date == next_pickup_date and x.type == waste_type for x in entries)
            if not found:
                entries.append(
                    Collection(date=next_pickup_date, t=waste_type, icon=icon)
                )
        return entries
