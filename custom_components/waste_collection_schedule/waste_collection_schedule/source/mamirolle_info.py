import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Mairie de Mamirolle"
DESCRIPTION = "Source script for mamirolle.info"
COUNTRY = "fr"
URL = "http://mamirolle.info/"

TEST_CASES = {
    "TestSource": {},
    "IgnoredArgument": {
        "_": ""
    }
}

ICON_MAP = {
    "Poubelle grise": "mdi:trash-can",
    "Poubelle jaune": "mdi:recycle",
}

MONTH_NAMES = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


class Source:
    def __init__(self, _=None):
        pass

    def fetch(self):
        now = datetime.datetime.now()
        # get list of regions and weblinks
        page = requests.get(URL)
        # A lenient HTML parser is need
        soup = BeautifulSoup(page.text.replace("<![endif]", ""), "html.parser")
        trash_domestic = soup.find("i", class_="poubelle-grise")
        _, day, month = trash_domestic.next_sibling.string.split()
        date_domestic = now.replace(month=MONTH_NAMES.index(month), day=int(day)).date()
        if date_domestic < now.date():
            date_domestic = date_domestic.replace(year=date_domestic.year + 1)

        trash_recycle = soup.find("i", class_="poubelle-jaune")
        _, day, month = trash_recycle.next_sibling.string.split()
        date_recycle = now.replace(month=MONTH_NAMES.index(month), day=int(day)).date()
        if date_recycle < now.date():
            date_recycle = date_recycle.replace(year=date_recycle.year + 1)

        entries = [
            Collection(
                date=date_domestic,
                t="Poubelle grise",
                icon=ICON_MAP.get("Poubelle grise"),
            ),
            Collection(
                date=date_recycle,
                t="Poubelle jaune",
                icon=ICON_MAP.get("Poubelle jaune"),
            ),
        ]  # List that holds collection schedule

        return entries
