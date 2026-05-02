import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen"
DESCRIPTION = (
    "Source for tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen."
)
URL = "https://tonnenleerung.de"
TEST_CASES = {
    "nd-sob/neuburg-donau/abbevillestrasse/": {
        "url": "nd-sob/neuburg-donau/abbevillestrasse/"
    },
    "aic-fdb/affing/": {"url": "https://tonnenleerung.de/aic-fdb/affing"},
    "nd-sob/schrobenhausen/albertus-magnus-weg/": {
        "url": "/nd-sob/schrobenhausen/albertus-magnus-weg/"
    },
}


ICON_MAP = {
    "grau4": "mdi:trash-can",
    "grau": "mdi:trash-can",
    "Bio": "mdi:leaf",
    "blau": "mdi:package-variant",
    "gelb": "mdi:recycle",
}


API_URL = "https://tonnenleerung.de/{url}"

# Map JSON keys to bin types
JSON_KEY_TO_TYPE = {
    "blau": "blau",
    "gelb": "gelb",
    "braun": "Bio",
    "grau": "grau",
    "grau4": "grau4",
}

PARAM_TRANSLATIONS = {
    "de": {
        "url": "URL",
    }
}


class Source:
    def __init__(self, url: str):
        self._url: str = url
        if "tonnenleerung.de" in self._url:
            self._url = self._url.split("tonnenleerung.de")[1]
        if self._url.startswith("/"):
            self._url = self._url[1:]

    def fetch(self):
        r = requests.get(API_URL.format(url=self._url))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        script_tag = soup.find(
            "script", {"type": "application/json", "id": "leerungsdaten"}
        )
        if not script_tag:
            raise ValueError("Could not find waste collection data in HTML")

        data = json.loads(script_tag.string)

        entries = []
        for key, dates in data.items():
            bin_type = JSON_KEY_TO_TYPE.get(key)
            if not bin_type:
                continue

            for date_str in dates:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                icon = ICON_MAP.get(bin_type)
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
