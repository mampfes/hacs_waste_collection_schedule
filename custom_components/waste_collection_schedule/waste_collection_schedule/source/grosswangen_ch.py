import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Grosswangen"
DESCRIPTION = " Source for 'Grosswangen, CH'"
URL = "https://www.grosswangen.ch"
TEST_CASES = {"TEST": {}}

ICON_MAP = {
    "Grüngutabfuhr": "mdi:leaf",
    "Kehricht-Aussentour": "mdi:trash-can-outline",
    "Kartonsammlung": "mdi:recycle",
    "Altpapiersammlung": "mdi:newspaper-variant-multiple-outline",
    "Häckselservice": "mdi:leaf-off",
    "Alteisensammlung und Sammlung elektronischer Geräte": "mdi:desktop-classic",
    "Zusätzliche Gratis-Laubabfuhr": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self):
        self = None

    def fetch(self):

        r = requests.get(
            "https://www.grosswangen.ch/institution/details/abfallsammlungen"
        )

        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        entries = []

        for tag in soup.find_all(class_="InstList-institution InstDetail-termin"):
            for typ in tag.find_all("strong"):
                # print(typ.string)
                waste_type = typ.string
            for date in tag.find_all("span", class_="mobile"):
                # print(date.string[-8:])
                waste_date = datetime.strptime(date.string[-8:], "%d.%m.%y").date()

            entries.append(Collection(waste_date, waste_type, ICON_MAP.get(waste_type)))

        return entries
