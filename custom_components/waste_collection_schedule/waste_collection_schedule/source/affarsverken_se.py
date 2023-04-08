import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import datetime

TITLE = "Affärsverken"
DESCRIPTION = "Source for Affärsverken."
URL = "https://www.affarsverken.se/"

TEST_CASES = {
    "Albatrossvägen 5, Ramdala": {"address": "Albatrossvägen 5, Ramdala"},
    "Amandas Väg 11, Sturkö": {"address": "Amandas Väg 11, Sturkö"},
    "Uddabygd 107, Rödeby": {"address": "Uddabygd 107, Rödeby"},
    "Zenitavägen 2, Hasslö": {"address": "Zenitavägen 2, Hasslö"},
}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:leaf",
    "Trädgårdsavfall": "mdi:tree"
}

API_URL = "https://kundapi.affarsverken.se/api/v1/open-api/"

class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self):
        args = {
            "address": self._address
        }

        r = requests.post(f"{API_URL}login", params={"BrandName": "Affarsverken"})
        r.raise_for_status()
        headers = {"Authorization": "Bearer " + r.text}

        r = requests.get(f"{API_URL}waste/buildings/search", params=args, headers=headers)
        data = r.json()
        building_query = data[0]["query"]
        
        r = requests.get(f"{API_URL}waste/buildings/" + building_query, headers=headers)
        r.raise_for_status()
        services = r.json()["services"]

        entries = []
        for service in services:
            if not service["nextPickup"]:
                continue
            date = datetime.datetime.strptime(service["nextPickup"], "%Y-%m-%d").date()
            icon = ICON_MAP.get(service["title"])  # Collection icon
            type = service["title"]
            
            # add bin size to description
            if "binSize" in service and "binSizeUnit" in service:
                type += ", " + str(service["binSize"]).replace(".0", "") + " "+ str(service["binSizeUnit"])
            type = type.strip()
            
            entries.append(Collection(date=date, t=type, icon=icon))

        return entries
