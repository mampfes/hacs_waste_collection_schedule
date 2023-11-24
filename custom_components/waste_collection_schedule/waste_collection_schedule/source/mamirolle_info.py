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
        trash_recycle = soup.find("i", class_="poubelle-jaune")

        entries = []  # List that holds collection schedule
        for trash, label in [(trash_domestic, "Poubelle grise"), (trash_recycle, "Poubelle jaune")]:
            _, day, month = trash.next_sibling.string.split()
            date = now.replace(month=MONTH_NAMES.index(month) + 1, day=int(day)).date()
            if date < now.date():
                date = date.replace(year=date.year + 1)

            entries.append(Collection(
                date=date,
                t=label,
                icon=ICON_MAP.get(label),
            ))

        return entries
