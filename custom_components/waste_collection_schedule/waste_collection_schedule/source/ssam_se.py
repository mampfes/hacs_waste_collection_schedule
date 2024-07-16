from datetime import datetime
import json
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "SSAM"
DESCRIPTION = "Source for SSAM waste collection."
URL = "https://ssam.se"
TEST_CASES = {
    "Home": {"street_address": "Asteroidvägen 1, Växjö"},
    "Bostadsrätt": {"street_address": "Långa Gatan 29 -81, Växjö"},
    "Slambrunn": {"street_address": "Svanebro Ormesberga, Ör"},
}
_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        params = {"searchText": self._street_address}
        response = requests.post(
            "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/SearchAdress",
            params=params,
            timeout=30,
        )

        address_data = json.loads(response.text)
        address = None

        if address_data and len(address_data) > 0:
            address = address_data["Buildings"][0]

        if not address:
            return []

        params = {"address": address}
        response = requests.get(
            "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule",
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

            if item["WasteType"] == "FNI1":
                waste_type = (
                    "Kärl 1, "
                    + item["BinType"]["ContainerType"]
                    + " "
                    + str(item["BinType"]["Size"])
                    + item["BinType"]["Unit"]
                )
                icon = "mdi:trash-can"
            elif item["WasteType"] == "FNI2":
                waste_type = (
                    "Kärl 2, "
                    + item["BinType"]["ContainerType"]
                    + " "
                    + str(item["BinType"]["Size"])
                    + item["BinType"]["Unit"]
                )
                icon = "mdi:trash-can"
            elif item["BinType"]["Code"] == "KM140":
                waste_type = "Matpåsar"
                icon = "mdi:recycle"
            else:
                waste_type = (
                    item["WasteType"]
                    + " "
                    + item["BinType"]["ContainerType"]
                    + " "
                    + str(item["BinType"]["Size"])
                    + item["BinType"]["Unit"]
                )
                icon = "mdi:trash-can"
                if item["WasteType"] == "Trädgårdsavfall":
                    icon = "mdi:leaf"
            found = 0
            for x in entries:
                if x.date == next_pickup_date and x.type == waste_type:
                    found = 1
            if found == 0:
                entries.append(
                    Collection(date=next_pickup_date, t=waste_type, icon=icon)
                )
        return entries
