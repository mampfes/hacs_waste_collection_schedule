import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Grosswangen"
DESCRIPTION = " Source for 'Grosswangen, CH'"
URL = "https://www.grosswangen.ch"
TEST_CASES: dict[str, dict[str, str]] = {"TEST": {}}

ICON_MAP = {
    "Grüngutabfuhr": Icons.ORGANIC,
    "Kehricht-Aussentour": Icons.GENERAL_WASTE,
    "Kartonsammlung": Icons.PAPER,
    "Altpapiersammlung": Icons.PAPER,
    "Häckselservice": Icons.GARDEN,
    "Alteisensammlung und Sammlung elektronischer Geräte": Icons.ELECTRONICS,
    "Zusätzliche Gratis-Laubabfuhr": Icons.ORGANIC,
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self):
        pass

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
