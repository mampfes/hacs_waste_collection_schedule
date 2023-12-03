from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North / Middle Bohuslän - Rambo AB"
DESCRIPTION = "Source for North / Middle Bohuslän - Rambo AB."
URL = "https://www.rambo.se/"
TEST_CASES = {
    "Grebbestad Ö.långgat./Storg., Grebbestad": {
        "address": "Grebbestad Ö.långgat./Storg., Grebbestad"
    },
    "Grebbestadsvägen 6, Tanumshede": {"address": "Grebbestadsvägen 6, Tanumshede"},
    "Torgvägen 1, Centrum, Hedekas": {"address": "Torgvägen 1, Centrum, Hedekas"},
    "Örekilsvägen Munkedals Reningsverk 10, Munkedal": {
        "address": "Örekilsvägen Munkedals Reningsverk 10, Munkedal"
    },
    "Storgatan 39, Smögen": {"address": "Storgatan 39, Smögen"},
}


ICON_MAP = {
    "Hushållsavfall": "mdi:trash-can",
    "Matavfall": "mdi:leaf",
    "Kärl": "mdi:trash-can",
}


API_URL = "https://rambo.se/wp-json/app/v1/{}"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "X-App-Identifier": "www.rambo.se/hamtdag",
}


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self):
        args = {
            "address": self._address.split(",")[0],
        }

        # get json file
        r = requests.get(API_URL.format("address-flat"), params=args, headers=HEADERS)
        r.raise_for_status()

        data = r.json()

        plant_number = None
        for hit in data:
            if (
                "address" in hit
                and hit["address"].strip().lower() == self._address.strip().lower()
            ):
                plant_number = hit["plant_number"].replace(" ", "+")
                break

        if not plant_number:
            raise Exception(
                "Address not found write it exactly as it is on the website"
            )

        r = requests.get(
            API_URL.format("next-pickup-web"),
            params={"plant-number": plant_number},
            headers=HEADERS,
        )

        r.raise_for_status()
        data = r.json()

        entries = []
        for d in data["types"]:
            date = datetime.strptime(d["pickup_date"], "%Y-%m-%d").date()
            icon = ICON_MAP.get(d["type"])  # Collection icon
            type = d["type"]
            entries.append(Collection(date=date, t=type, icon=icon))

        return entries
