# coding: utf-8
from datetime import datetime
import json
from urllib.parse import urlencode

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Region Gotland"
DESCRIPTION = "Source for Region Gotland waste collection."
URL = "https://edpfuture.gotland.se"
TEST_CASES = {
    "Dummy": {"uprn": "0000000000"},
}

class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        query_params = urlencode({"address": '(' + self._uprn + ')'})
        response = requests.get(
            "https://edpfuture.gotland.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule?{}"
            .format(query_params)
        )
        data = json.loads(response.text)

        entries = []
        for item in data["RhServices"]:
            waste_type = item["WasteType"]
            icon = "mdi:trash-can"
            if waste_type == "Matavfall":
                icon = "mdi:leaf"
            next_pickup = item["NextWastePickup"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            entries.append(
                Collection(date=next_pickup_date, t=waste_type, icon=icon)
            )

        return entries
