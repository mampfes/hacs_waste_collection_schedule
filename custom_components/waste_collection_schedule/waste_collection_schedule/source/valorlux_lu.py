import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentRequiredWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Valorlux"
DESCRIPTION = "Source for Valorlux waste collection."
URL = "https://www.valorlux.lu"
TEST_CASES = {
    "Mersch": {"city": "Mersch"},
    "Luxembourg City (Tour 1)": {"city": "Luxembourg", "zone": "Tour 1"},
    "Unknown City": {"city": "Unknown", "zone": None},
}

API_URL = "https://www.valorlux.lu/manager/mod/valorlux/valorlux/all"
ICON_MAP = {
    "PMC": "mdi:recycle",
}


class Source:
    def __init__(self, city: str | None = None, zone: str | None = None):
        self._city = city
        self._zone = zone

    def fetch(self):
        r = requests.get(API_URL)
        r.raise_for_status()
        data = r.json()
        cities = data.get("cities", {})

        # Step 1: If no city is provided, raise an exception with a list of all cities
        if self._city is None:
            city_names = sorted(list(cities.keys()))
            raise SourceArgumentRequiredWithSuggestions("city", city_names)

        # Step 2: If city is provided, check if it's valid
        if self._city not in cities:
            city_names = sorted(list(cities.keys()))
            raise SourceArgumentNotFoundWithSuggestions("city", self._city, city_names)

        # Step 3: Check for zones/tours for the selected city
        city_data = cities[self._city]
        zones = list(city_data.keys())

        # If there are multiple zones and none is selected, raise an exception with the list of zones
        if len(zones) > 1 and self._zone is None:
            raise SourceArgumentRequiredWithSuggestions("zone", zones)
        
        # If a zone is selected, check if it's valid
        if self._zone and self._zone not in zones:
            raise SourceArgumentNotFoundWithSuggestions("zone", self._zone, zones)

        # Step 4: Fetch the actual collection dates
        if self._zone:
            dates = city_data[self._zone]
        else:
            # If there's only one zone, or no zone is needed, take the first one
            dates = next(iter(city_data.values()))

        collections = []
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