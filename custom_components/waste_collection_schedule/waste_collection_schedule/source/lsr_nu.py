import json
import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Landskrona - Svalövs Renhållning"
DESCRIPTION = "Source for LSR waste collection."
COUNTRY = "se"
URL = "https://www.lsr.nu"
TEST_CASES = {
    "Home": {"street_address": "Saxtorpsvägen 115, Annelöv"},
    "Polisen": {"street_address": "Herrevadsgatan 11, Svalöv"},
}

# {
#   "containerId": "12C",
#   "date": "2024-01-03T00:00:00",
#   "title": "Hämtning av restavfall (kärl 370 liter)",
#   "typeOfWaste": "REST",
#   "typeOfWasteDescription": "Restavfall"
# },
# {
#   "containerId": "13B",
#   "date": "2024-01-03T00:00:00",
#   "title": "Hämtning av matavfall (kärl 140 liter)",
#   "typeOfWaste": "MAT",
#   "typeOfWasteDescription": "Matavfall"
# }

class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        response = requests.get(
            "https://minasidor.lsr.nu/api/api/external/schedule/" + self._street_address,
        )

        data = response.json()

        entries = []
        for item in data:
            waste_type = item["typeOfWasteDescription"]
            icon = "mdi:trash-can"
            if waste_type == "Trädgårdsavfall":
                icon = "mdi:leaf"
            next_pickup = item["date"]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
