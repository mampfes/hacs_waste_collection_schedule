import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Gmina Środa Śląska"
DESCRIPTION = "Source for Gmina Środa Śląska, Poland"
URL = "https://waste-collection.sciana.pro"
TEST_CASES = {
    "Ciechów": {"location_id": 3},
}

ICON_MAP = {
    "Zmieszane komunalne": "mdi:trash-can",  # Mixed
    "Tworzywa sztuczne": "mdi:recycle",  # Plastic
    "Odpady kuchenne ulegające biodegradacji": "mdi:leaf",  # Organic
    "Papier": "mdi:file-outline",  # Paper
    "Szkło": "mdi:glass-fragile",  # Glass
    "Odpady wielkogabarytowe": "mdi:sofa-single",
}

API_URL = "https://waste-collection.sciana.pro/api/v1/"
API_URL_JSON = ".json"


class Source:
    def __init__(self, location_id):
        self._location_id = location_id

    def fetch(self):
        api_response = requests.get(
            API_URL + str(self._location_id) + API_URL_JSON
        )

        entries = []

        kinds = api_response.json()["data"]["garbage_kinds"]

        for k in kinds:
            name = k["name"]
            for d in k["disposals"]:
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(d["date"], "%Y-%m-%d").date(),
                        t=name.capitalize(),
                        icon=ICON_MAP.get(name),
                    )
                )

        return entries
