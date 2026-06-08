import csv
from datetime import datetime

import requests

from ..collection import Collection
from ..icons import Icons

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
    "B": Icons.BIO_KITCHEN,
    "TKOS": Icons.GENERAL_WASTE,
    "TKOJ": Icons.GENERAL_WASTE,
    "BS": Icons.CHRISTMAS_TREE,
    "SHK": Icons.BIO_KITCHEN,
    "SHPA": Icons.PAPER,
    "SHPL": Icons.PLASTIC_PACKAGING,
    "SHS": Icons.GLASS,
    "NO": Icons.HAZARDOUS,
    "SKOL": Icons.GENERAL_WASTE,
    "SKOS": Icons.GENERAL_WASTE,
    "BIOJ": Icons.BIO_KITCHEN,
    "BIOS": Icons.BIO_KITCHEN,
    "BIOL": Icons.BIO_KITCHEN,
    "BIOSU": Icons.BIO_KITCHEN,
    "D2DPLAST": Icons.PLASTIC_PACKAGING,
    "D2DPLASTL": Icons.PLASTIC_PACKAGING,
    "D2DPLASTS": Icons.PLASTIC_PACKAGING,
    "D2DPAPIR": Icons.PAPER,
    "PET": Icons.GLASS,
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
