import csv
from datetime import datetime

import requests

from ..collection import Collection

TITLE = "Rudna u Prahy"
DESCRIPTION = "Source for Rudna u Prahy waste collection"
URL = "https://www.rudnamesto.cz/"
COUNTRY = "cz"
TEST_CASES = {
    "Even weeks": {"city_part": "Sudé týdny"},
    "Odd weeks": {"city_part": "Liché týdny"},
    "ALL": {"city_part": "Vše"},
}

WASTE_TYPES_URL = (
    "https://mesto-rudna.cz/odpadovy-kalendar/permanent/data_description.csv"
)
WASTE_DATES_URL = "https://mesto-rudna.cz/odpadovy-kalendar/permanent/data_calendar.csv"

ICON_MAP = {
    "B": "mdi:compost",
    "TKOS": "mdi:trash-can",
    "TKOJ": "mdi:trash-can",
    "BS": "mdi:pine-tree",
    "SHK": "mdi:pot",
    "SHPA": "mdi:note-text-outline",
    "SHPL": "mdi:recycle-variant",
    "SHS": "mdi:glass-fragile",
    "NO": "mdi:skull-scan",
    "SKOL": "mdi:trash-can",
    "SKOS": "mdi:trash-can",
    "BIOJ": "mdi:compost",
    "BIOS": "mdi:compost",
    "BIOL": "mdi:compost",
    "BIOSU": "mdi:compost",
    "D2DPLAST": "mdi:recycle-variant",
    "D2DPLASTL": "mdi:recycle-variant",
    "D2DPLASTS": "mdi:recycle-variant",
    "D2DPAPIR": "mdi:note-text-outline",
    "PET": "mdi:bottle-soda-outline",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Choose your service area from the published map https://www.rudnamesto.cz/odpadovy-kalendar/d-193572",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city_part": "Select whether waste is collected on even or odd weeks.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city_part": "Service area",
    },
}

CONFIG_FLOW_TYPES = {
    "city_part": {
        "type": "SELECT",
        "values": ["Sudé týdny", "Liché týdny", "Vše"],
        "multiple": False,
    }
}


class Source:
    def __init__(self, city_part=""):
        self._city_part = city_part

    def fetch(self):
        session = requests.Session()

        csv_content = session.get(WASTE_TYPES_URL, timeout=30).content.decode("utf-8")

        csv_lines = list(csv.reader(csv_content.splitlines(), delimiter=";"))

        waste_types = {}

        for row in csv_lines:
            mydict = {"desc": row[1], "icon": ICON_MAP.get(row[0], "mdi:trash-can")}
            waste_types[row[0]] = mydict

        csv_content = session.get(WASTE_DATES_URL, timeout=30).content.decode("utf-8")

        csv_lines = list(csv.reader(csv_content.splitlines(), delimiter=";"))

        entries = []

        format = "%Y-%m-%d"

        for row in csv_lines:
            if self._city_part.lower() == "s" and row[2] == "TKOJ":
                continue
            if self._city_part.lower() == "j" and row[2] == "TKOS":
                continue
            if self._city_part.lower() == "liché týdny" and row[2] in [
                "SKOS",
                "D2DPLASTS",
                "BIOSU",
            ]:
                continue
            if self._city_part.lower() == "sudé týdny" and row[2] in [
                "SKOL",
                "D2DPLASTL",
                "BIOL",
            ]:
                continue
            pickup_date = datetime.strptime(row[1], format)
            waste_type = waste_types[row[2]]["desc"]
            icon = waste_types[row[2]]["icon"]

            entries.append(Collection(date=pickup_date.date(), t=waste_type, icon=icon))

        return entries
