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

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "To get your LOCATION_ID go to https://waste-collection.sciana.pro and search for your address.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "location_id": "Unique location id (LOCATION_ID)",
    },
}


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
