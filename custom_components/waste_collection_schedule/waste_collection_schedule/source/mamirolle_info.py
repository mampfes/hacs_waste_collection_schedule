import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Mairie de Mamirolle"
DESCRIPTION = "Source script for mamirolle.info"
COUNTRY = "fr"
URL = "http://mamirolle.info/"

TEST_CASES = {
    "TestSource": {}
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

    def fetch(self):
        # get list of regions and weblinks
        page = requests.get(URL)
        # A lenient HTML parser is need
        soup = BeautifulSoup(page.text, "html5lib")

        trash_domestic = soup.find("i", class_="poubelle-grise")
        weekday, day, month = trash_domestic.next_sibling.string.split()
        date_domestic = datetime.datetime.now().replace(month=MONTH_NAMES.index(month), day=int(day)).date()

        trash_recycle = soup.find("i", class_="poubelle-jaune")
        weekday, day, month = trash_recycle.next_sibling.string.split()
        date_recycle = datetime.datetime.now().replace(month=MONTH_NAMES.index(month), day=int(day)).date()

        entries = [Collection(
            date=date_domestic,
            t="Poubelle grise",
            icon=ICON_MAP.get("Poubelle grise"),
        ), Collection(
            date=date_recycle,
            t="Poubelle jaune",
            icon=ICON_MAP.get("Poubelle jaune"),
        )]  # List that holds collection schedule

        return entries