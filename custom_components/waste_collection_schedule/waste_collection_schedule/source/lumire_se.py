from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Luleå"
DESCRIPTION = "Source for Luleå."
URL = "https://www.lumire.se/"
TEST_CASES = {
    "Ringgatan 20": {"address": "Ringgatan 20"},
    "Gårdsvägen 11": {"address": "GÅRDSVÄGEN 11, LULEÅ"},
    "Ymergatan 5": {"address": "Ymergatan 5"},
}


ICON_MAP = {
    "Restavfall": Icons.GENERAL_WASTE,
    "Matavfall": Icons.BIO_KITCHEN,
    "Porslin": Icons.BIO_KITCHEN,
    "Returpapper": Icons.PAPER,
    "Pappersförpackningar": Icons.PAPER,
    "Plastförpackningar": Icons.RECYCLING,
    "Metallförpackningar": Icons.METAL,
    "Färgade": Icons.GLASS,
    "Ofärgade": Icons.GLASS,
    "Ljuskällor": Icons.ELECTRONICS,
    "Småbatterier": Icons.BATTERY,
}

API_URL = "https://lumire.se/api/waste-pickup"
HEADERS = {"User-Agent": "Mozilla/5.0"}


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self) -> list[Collection]:
        # Först ber man snällt om ens buildingId hos våra vänner på Lumire
        r = requests.get(API_URL, params={"q": self._address}, headers=HEADERS)
        r.raise_for_status()
        search_results = r.json().get("addresses", [])

        if not search_results:
            raise ValueError(f"Address '{self._address}' not found")

        building_id = search_results[0].get("buildingId")

        # mha buildingId får man sitt faktiska schema
        r = requests.get(f"{API_URL}/{building_id}", headers=HEADERS)
        r.raise_for_status()
        pickup_data = r.json().get("data", [])

        entries = []
        for item in pickup_data:
            date_str = item.get("nextPickup")
            waste_type = item.get("fee", {}).get("waste_type") or item.get(
                "description", ""
            )

            if date_str:
                date_ = datetime.strptime(date_str, "%Y-%m-%d").date()

                icon = None
                for key, val in ICON_MAP.items():
                    if key.lower() in waste_type.lower():
                        icon = val
                        break

                entries.append(Collection(date_, waste_type, icon))

        return entries
