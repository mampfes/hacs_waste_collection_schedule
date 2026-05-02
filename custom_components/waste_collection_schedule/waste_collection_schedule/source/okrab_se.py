import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Ökrab Sophämntning"
DESCRIPTION = "Source script for Ökrab waste collection."
URL = "https://okrab.se"
TEST_CASES = {
    "Skolan": {"address": "SKOLGATAN 1, S:T OLOF"},
    "Butiken": {"address": "KILLEBACKEN 6, KIVIK"},
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        data = {"Address": self._address}
        response = requests.post(
            "https://minasidor.okrab.se/MinaSidor_API/api/external/schedulePost/",
            data=data,
        )

        r_data = json.loads(response.text)

        entries = []
        for item in r_data:
            waste_type = item["typeOfWasteDescription"]
            icon = "mdi:recycle"
            if waste_type == "Hushållsavfall":
                icon = "mdi:trash-can"
            elif waste_type == "Matavfall":
                icon = "mdi:leaf"
            item_date = datetime.fromisoformat(item["date"]).date()

            entries.append(Collection(date=item_date, t=waste_type, icon=icon))

        return entries
