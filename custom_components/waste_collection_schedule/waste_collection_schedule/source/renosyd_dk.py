from datetime import datetime
from typing import List

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Renosyd"
DESCRIPTION = "Renosyd collections for Skanderborg and Odder kommunes"
URL = "https://renosyd.dk"
TEST_CASES = {
    "TestCase1": {
        "house_number": "013000",
    },
    "TestCase2": {
        "house_number": "012000",
    },
    "TestCase3": {
        "house_number": "011000",
    },
}

ICON_MAP = {
    "RESTAFFALD": "mdi:trash-can",
    "PAPIR": "mdi:newspaper",
    "PAP": "mdi:archive",
    "EMBALLAGE": "mdi:recycle",
    "HAVEAFFALD": "mdi:leaf",  # Uncertain about this name, can't find an example
    "GLAS": "mdi:bottle-wine",
    "METAL": "mdi:wrench",
    "HÅRD PLAST": "mdi:bottle-soda-classic",
}


class Source:
    def __init__(self, house_number: str):
        self._api_url = f"https://skoda-selvbetjeningsapi.renosyd.dk/api/v1/toemmekalender?nummer={house_number}"

    def fetch(self) -> List[Collection]:
        response = requests.get(self._api_url)
        response.raise_for_status()
        data = response.json()

        entries = []

        for item in data:
            for toemning in item.get("planlagtetømninger", []):
                date = datetime.strptime(toemning["dato"], "%Y-%m-%dT%H:%M:%SZ").date()
                for fraktion in toemning["fraktioner"]:
                    entries.append(
                        Collection(
                            date=date,
                            t=fraktion,
                            icon=ICON_MAP.get(
                                fraktion.upper(), "mdi:trash-can-outline"
                            ),
                        )
                    )
        return entries
