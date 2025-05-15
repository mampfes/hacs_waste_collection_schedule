from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Luleå"
DESCRIPTION = "Source for Luleå."
URL = "https://www.lumire.se/"
TEST_CASES = {
    "Storgatan 2": {"address": "Storgatan 2"},
    "Ringgatan 20": {"address": "Ringgatan 20"},
}


ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:leaf",
    "Porslin": "mdi:coffee",
    "Returpapper": "mdi:package-variant",
    "Pappersförpackningar": "mdi:package-variant",
    "Plastförpackningar": "mdi:recycle",
    "Metallförpackningar": "mdi:recycle",
    "Färgade": "mdi:bottle-soda",
    "Ofärgade": "mdi:bottle-soda",
    "Ljuskällor": "mdi:lightbulb",
    "Småbatterier": "mdi:battery",
}


API_URL = "https://lumire.se/wp/wp-admin/admin-ajax.php"

HEADERS = {"User-Agent": "Mozilla/5.0"}


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self) -> list[Collection]:
        data = {"search_address": self._address, "action": "waste_pickup_form"}

        r = requests.post(API_URL, data=data, headers=HEADERS)
        r.raise_for_status()
        if "Den adress du har angivit finns inte i v\u00e5rt system" in r.text:
            raise ValueError("Address not found")

        data_list = (
            r.text.encode()
            .decode("unicode_escape")
            .replace(r"\/", "/")
            .strip('"')
            .split("<br>")
        )

        collections = zip(data_list[::2], data_list[1::2])

        entries = []
        for bin_type, date_str in collections:
            date_str = date_str.replace(":", "").strip()
            date_ = datetime.strptime(date_str, "%Y-%m-%d").date()
            bin_type = bin_type.replace("Nästa tömning för", "").strip()
            icon = ICON_MAP.get(bin_type.split()[0])
            entries.append(Collection(date_, bin_type, icon))

        return entries
