from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Luleå"
DESCRIPTION = "Source for Luleå."
URL = "https://www.lumire.se/"
TEST_CASES = {
    "This should fail": {"address": "Storgatan 2"},
    "Ringgatan 20": {"address": "Ringgatan 20"},
    "Gårdsvägen 11": {"address": "GÅRDSVÄGEN 11, LULEÅ"},
    "Ymergatan 5": {"address": "Ymergatan 5"}
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
        if "Den adress du har angivit finns inte" in r.text:
            raise ValueError("Address not found")

        clean_html = r.text.encode().decode("unicode_escape").replace(r"\/", "/").strip('"')

        soup = BeautifulSoup(clean_html, "html.parser")
        results = soup.find("div", {"class": "waste-result-list"})
        collections = results.find_all("div")

        entries = []
        for c in collections:
            parts = c.text.split(":")
            try:
                date_ = datetime.strptime(parts[0].strip(), "%Y-%m-%d").date()
            except:
                # There is a bug in the API that makes the date return as thee string "Array", so we simply ignore this failure.
                continue

            bin_type = parts[1].strip()
            icon = ICON_MAP.get(bin_type.split(",")[0])

            entries.append(Collection(date_, bin_type, icon))

        return entries
