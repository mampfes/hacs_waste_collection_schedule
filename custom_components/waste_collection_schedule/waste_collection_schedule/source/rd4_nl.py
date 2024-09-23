from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Rd4"
DESCRIPTION = "Source for Rd4."
URL = "https://rd4.nl/"
TEST_CASES = {"6417 AT 32": {"postal_code": "6417 AT", "house_number": 32}}


ICON_MAP = {
    "pmd": "mdi:recycle",
    "gft": "mdi:leaf",
    "residual_waste": "mdi:trash-can",
    "paper": "mdi:newspaper",
    "pruning_waste": "mdi:leaf",
    "best_bag": "mdi:bag-personal",
    "christmas_trees": "mdi:christmas-tree",
}


API_URL = "https://data.rd4.nl/api/v1/waste-calendar"


class Source:
    def __init__(self, postal_code: str, house_number: str | int):
        self._postal_code: str = postal_code
        self._house_number: str | int = house_number

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        year = now.year
        entries = []
        exception = None
        try:
            entries = self._get_collections(year)
        except Exception as e:
            # Do not fail in december to try to fetch next year
            if now.month != 12:
                raise
            exception = e

        if now.month != 12:
            return entries

        # Fetch next year in December
        year += 1
        try:
            return entries + self._get_collections(year)
        except Exception:
            if exception:
                raise exception
            return entries

    def _get_collections(self, year) -> list[Collection]:
        args = {
            "postal_code": self._postal_code,
            "house_number": self._house_number,
            "year": year,
        }

        # get json file
        r = requests.get(API_URL, params=args)
        r.raise_for_status()
        data = r.json()
        if not (
            "data" in data
            and "items" in data["data"]
            and len(data["data"]["items"]) > 0
        ):
            raise ValueError("No data found, check your arguments")

        entries = []

        for item in data["data"]["items"]:
            for collection in item:
                date_ = datetime.strptime(collection["date"], "%Y-%m-%d").date()
                bin_type = collection["type"]

                icon = ICON_MAP.get(bin_type)  # Collection icon
                entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
