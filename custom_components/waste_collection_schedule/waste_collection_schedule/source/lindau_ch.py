import json
import re
import unicodedata
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Lindau"
DESCRIPTION = "Source for Lindau waste collection."
URL = "https://www.lindau.ch"
TEST_CASES = {
    "Tagelswangen": {"city": "Tagelswangen"},
    "Grafstal": {"city": "190"},
}


ICON_MAP = {
    "kehricht": Icons.GENERAL_WASTE,
    "grungut": Icons.ORGANIC,
    "hackseldienst": Icons.GARDEN,
    "papier und karton": Icons.PAPER,
    "altmetalle": Icons.METAL,
    "sonderabfall": Icons.HAZARDOUS,
}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
    }
}


class Source:
    def __init__(self, city):
        self._city = city

    def fetch(self):
        response = requests.get("https://www.lindau.ch/abfalldaten")

        html = BeautifulSoup(response.text, "html.parser")

        table = html.find("table", attrs={"id": "icmsTable-abfallsammlung"})
        data = json.loads(table.attrs["data-entities"])

        entries = []
        for item in data["data"]:
            if (
                self._city in item["abfallkreisIds"]
                or self._city in item["abfallkreisNameList"]
            ):
                # The `*-sort` fields are now obfuscated ("#1713..."), so read
                # the plain display fields instead.
                next_pickup = re.search(r"\d{2}\.\d{2}\.\d{4}", item["_anlassDate"])
                if next_pickup is None:
                    continue
                next_pickup_date = datetime.strptime(
                    next_pickup.group(0), "%d.%m.%Y"
                ).date()

                waste_type = BeautifulSoup(item["name"], "html.parser").text
                icon_key = (
                    unicodedata.normalize("NFKD", waste_type)
                    .encode("ascii", "ignore")
                    .decode()
                    .lower()
                )
                icon = next(
                    (icon for key, icon in ICON_MAP.items() if key in icon_key),
                    Icons.GENERAL_WASTE,
                )

                entries.append(
                    Collection(
                        date=next_pickup_date,
                        t=waste_type,
                        icon=icon,
                    )
                )

        return entries
