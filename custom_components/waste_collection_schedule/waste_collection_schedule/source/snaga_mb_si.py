from datetime import date, datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Snaga Maribor"
DESCRIPTION = "Source for Snaga Maribor."
URL = "https://snaga-mb.si/"
TEST_CASES = {
    "Ruska ulica 24": {"street": "Ruska ulica", "house_number": 24},
}


BIN_TYPES = {
    "O": "Ost.",
    "B": "Bio.",
    "U": "Emb.",
    "P": "Pap.",
    "S": "Stek.",
}
ICON_MAP = {
    "O": "mdi:trash-can",
    "B": "mdi:leaf",
    "U": "mdi:recycle",
    "P": "mdi:newspaper",
    "S": "mdi:glass-cocktail",
}

BASE_URL = "https://arhiv.snaga-mb.si/mso"
ADDRESS_ID_URL = f"{BASE_URL}/tmRSkjpgG.php"
COLLECTION_URL = f"{BASE_URL}/tmRSk.php"


class Source:
    def __init__(self, street: str, house_number: str | int):
        self._street: str = street
        self._house_number: str | int = house_number

    def fetch(self) -> list[Collection]:
        args = {
            "Naziv": self._street,
            "HS": self._house_number,
            "IDo": "0",
            "_": int(datetime.now().timestamp() * 1000),
        }
        r = requests.get(ADDRESS_ID_URL, params=args)
        r.raise_for_status()
        if r.text == "null" or not r.json():
            raise Exception("Invalid address")

        entries = []
        for id in r.json():
            address_id = id["OM"]
            r = requests.get(
                COLLECTION_URL,
                params={"sql": address_id, "_": int(datetime.now().timestamp() * 1000)},
            )

            for collection in r.json():
                day = int(collection["Dan"])
                month = int(collection["Mesec"])
                year = int(collection["Leto"])
                date_ = date(year, month, day)
                type_char = collection["Odp"]
                bin_type = BIN_TYPES.get(type_char, type_char)
                icon = ICON_MAP.get(type_char)
                entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
