import requests
import json

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Republic Services"
DESCRIPTION = "Source for Republic Services Collection."
URL = "https://www.republicservices.com"
COUNTRY = "us"
TEST_CASES = {
    "Scott Country Clerk": {"street_address": "101 E Main St, Georgetown, KY 40324"},
    "Branch County Clerk": {"street_address": "31 Division St. Coldwater, MI 49036"}
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        response1 = requests.get(
            "https://www.republicservices.com/api/v1/addresses",
            params={"addressLine1": self._street_address},
        )

        address_hash = json.loads(response1.text)["data"][0]["addressHash"]

        response2 = requests.get(
            "https://www.republicservices.com/api/v1/publicPickup",
            params={"siteAddressHash": address_hash},
        )

        r_json = json.loads(response2.text)["data"]

        entries = []

        for x in r_json:
            if hasattr(r_json[x], "__iter__"):
                for item in r_json[x]:
                    waste_type = item["wasteTypeDescription"]
                    container_type = item["containerType"]
                    icon = "mdi:trash-can"
                    if waste_type == "Recycle":
                        icon = "mdi:recycle"
                        if container_type == "YC":
                            waste_type = "Yard Waste"
                            icon = "mdi:sprout"
                    for day in item["nextServiceDays"]:
                        next_pickup = day
                        next_pickup_date = datetime.fromisoformat(next_pickup).date()
                        entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
