from datetime import datetime

import cloudscraper
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Valorlux"
DESCRIPTION = "Source for Valorlux waste collection."
URL = "https://www.valorlux.lu"
TEST_CASES = {
    "Mersch": {"commune": "Mersch"},
    "Luxembourg City (Tour 1)": {"commune": "Luxembourg", "zone": "Tour 1"},
    "Parc Hosingen": {"commune": "Parc Hosingen"},
    "Unknown Commune": {"commune": "Unknown", "zone": None},
}

API_URL = "https://www.valorlux.lu/api/calendar/all"
ICON_MAP = {
    "PMC": "mdi:recycle",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.valorlux.lu/",
    "Origin": "https://www.valorlux.lu",
}


class Source:
    def __init__(self, commune: str | None = None, zone: str | None = None):
        self._commune = commune
        self._zone = zone

    def fetch(self):
        scraper = cloudscraper.create_scraper()
        scraper.headers.update(HEADERS)
        r = scraper.get(API_URL)
        r.raise_for_status()
        data = r.json()

        # The API returns two dictionaries of locations, 'cities' and 'otherAddresses'
        # Merge them into a single dictionary for processing
        communes = data.get("cities", {})
        other_communes = data.get("otherAddresses", {})
        communes.update(other_communes)

        # Step 1: If no commune is provided, raise an exception with a list of all communes
        if self._commune is None:
            commune_names = sorted(list(communes.keys()))
            raise SourceArgumentRequiredWithSuggestions("commune", None, commune_names)

        # Step 2: If commune is provided, check if it's valid
        if self._commune not in communes:
            commune_names = sorted(list(communes.keys()))
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self._commune, commune_names
            )

        # Step 3: Check for zones/tours for the selected commune
        commune_data = communes[self._commune]
        zones = list(commune_data.keys())

        # If there are multiple zones and none is selected, raise an exception with the list of zones
        if len(zones) > 1 and self._zone is None:
            raise SourceArgumentRequiredWithSuggestions("zone", None, zones)

        # If a zone is selected, check if it's valid
        if self._zone and self._zone not in zones:
            raise SourceArgumentNotFoundWithSuggestions("zone", self._zone, zones)

        # Step 4: Fetch the actual collection dates
        if self._zone:
            dates = commune_data[self._zone]
        else:
            # If there's only one zone, or no zone is needed, take the first one
            dates = next(iter(commune_data.values()))

        collections = []
        for date_str in dates:
            # Use %y for 2-digit year
            date = datetime.strptime(date_str, "%d/%m/%y").date()
            collections.append(
                Collection(
                    date=date,
                    t="Valorlux Bag (PMC)",
                    icon=ICON_MAP.get("PMC"),
                )
            )

        return collections
