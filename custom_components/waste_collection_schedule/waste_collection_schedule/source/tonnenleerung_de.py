import json
import re
from datetime import datetime

import requests
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

EXTRA_INFO = [
    {
        "name": "LK Aichach-Friedberg",
        "url": "https://tonnenleerung.de/aic-fdb/",
    },
    {
        "name": "LK Neuburg-Schrobenhausen",
        "url": "https://tonnenleerung.de/nd-sob/",
    },
]


# Array names included in the html file
ARRAY_NAMES = ["blauArray", "gelbArray", "grauArray", "braunArray", "grau4Array"]

REGEX_TEMPLATE = r"{array_name}\s?=\s?\[[,\"\-\d]*\]"

# Array names to names shown on the frontend
NAME_2_TYPE = {
    "blauArray": "blau",
    "gelbArray": "gelb",
    "grauArray": "grau",
    "braunArray": "Bio",
    "grau4Array": "grau4",
}


class Source:
    def __init__(self, url: str):
        self._url: str = url
        if "tonnenleerung.de" in self._url:
            self._url = self._url.split("tonnenleerung.de")[1]
        if self._url.startswith("/"):
            self._url = self._url[1:]

    def fetch(self):
        # get json file
        r = requests.get(API_URL.format(url=self._url))
        r.raise_for_status()

        entries = []

        for array_name in ARRAY_NAMES:
            array = re.search(REGEX_TEMPLATE.format(array_name=array_name), r.text)
            if not array:
                continue
            bin_type = NAME_2_TYPE[array_name]
            dates = json.loads(array.group(0).split("=")[1])
            for date_str in dates:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                icon = ICON_MAP.get(bin_type)  # Collection icon

                entries.append(Collection(date=date, t=bin_type, icon=icon))
        return entries
