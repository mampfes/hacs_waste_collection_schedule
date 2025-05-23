from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Avfall & Återvinning Skaraborg"
DESCRIPTION = "Source for Skaraborg."
URL = "https://avfallskaraborg.se/"
TEST_CASES = {
    "Granängsvägen 1, Skövde": {"address": "Granängsvägen 1", "city": "Skövde"},
    "Skaraborgs tingsrätt": {"address": "Eric Ugglas Plats 2", "city": "Skövde"},
}

ICON_MAP = {
    "Matavfall": "mdi:leaf",
    "Brännbart": "mdi:fire",
    "Matavfall/Restavfall": "mdi:trash-can",
    "Plast/Kartong": "mdi:package",
    "Färgat glas/Ofärgat glas": "mdi:bottle-soda",
}

SEARCH_URL = "https://gullspang.avfallsapp.se/api/nova/v1/next-pickup/search"
DATA_URL = "https://gullspang.avfallsapp.se/api/nova/v1/next-pickup/address"


class Source:
    def __init__(self, address: str, city: str):
        self._address: str = address
        self._city: str = city

    def fetch(self) -> list[Collection]:
        headers = {
            "Authorization": "Bearer J6lD4hVH8pRMQZeBSoCvtCZj1V0wvgg0QvBqSDTH9fce942d",
            "X-App-Identifier": "70bae483-3268-4875-93f5-14f2274ec7cb",
        }
        search_params = {"address": self._address}
        search_request = requests.get(SEARCH_URL, params=search_params, headers=headers)
        search_request.raise_for_status()

        search_results = search_request.json()
        if not search_results:
            raise Exception("No addresses found")

        data = {"plant_id": self._find_plant_id(search_results)}
        data_request = requests.post(DATA_URL, data, headers=headers)
        data_request.raise_for_status()

        data_results = data_request.json()
        assert data_results.get("address") == self._address
        assert data_results.get("city") == self._city

        entries = []
        for _, bin_data in data_results.get("bins").items():
            date_ = datetime.strptime(bin_data["pickup_date"], "%Y-%m-%d").date()
            bin_type = bin_data["type"]
            icon = ICON_MAP.get(bin_type)
            entries.append(Collection(date_, bin_type, icon))

        return entries

    def _find_plant_id(self, search_results) -> str:
        try:
            return next(
                x["plant_number"]
                for x in search_results[self._city]
                if x["zip_city"] == self._city and x["address"] == self._address
            )
        except StopIteration:
            raise Exception("Can't find plant id for address")
