import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Valorlux"
DESCRIPTION = "Source for Valorlux waste collection."
URL = "https://www.valorlux.lu"
TEST_CASES = {
    "Mersch": {"city": "Mersch"},
    "Luxembourg": {"city": "Luxembourg", "zone": "1"},
}

API_URL = "https://www.valorlux.lu/manager/mod/valorlux/valorlux/all"
ICON_MAP = {
    "PMC": "mdi:recycle",
}


class Source:
    def __init__(self, city, zone=None):
        self._city = city
        self._zone = zone

    def fetch(self):
        r = requests.get(API_URL)
        r.raise_for_status()
        data = r.json()

        if self._city not in data["cities"]:
            raise Exception(f"City not found: {self._city}")

        city_data = data["cities"][self._city]
        
        collections = []
        
        # In many cases, there is only one entry, but for cities with zones, there can be multiple
        if self._zone:
            key = f"Tour {self._zone}"
            if key not in city_data:
                raise Exception(f"Zone {self._zone} not found for city {self._city}")
            dates = city_data[key]
        else:
            # Take the first entry if no zone is specified
            dates = next(iter(city_data.values()))


        for date_str in dates:
            date = datetime.strptime(date_str, "%d/%m/%Y").date()
            collections.append(
                Collection(
                    date=date,
                    t="PMC",
                    icon=ICON_MAP.get("PMC"),
                )
            )

        return collections
