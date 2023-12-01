import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Mairie de Vern sur Seiche"
DESCRIPTION = "Poubelle jaune tous les jeudis des semaines impaires, Poubelle grise tous les lundi. Lorsque le lundi ou le jeudi est un jour férié, les deux sont décalées d'un jour"
COUNTRY = "fr"
URL = "https://www.vernsurseiche.fr/accueil/cadre-de-vie/proprete-dechets/collecte-des-dechets"

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
        now = datetime.datetime.now()

        # Determine the waste type based on the current day
        waste_type = None
        if now.weekday() == 0:  # Monday
            waste_type = "Poubelle grise"
        elif now.weekday() == 3 and now.isocalendar()[1] % 2 == 1:  # Thursday and odd week
            waste_type = "Poubelle jaune"

        if waste_type:
            # Adjustments for special cases in 2023
            if waste_type == "Poubelle jaune" and day == "17" and month == "août":
                day = "18"
            elif waste_type == "Poubelle grise" and day == "25" and month == "décembre":
                day = "26"

            # Adjustments for special cases in 2024
            if waste_type == "Poubelle grise" and day == "1" and month == "janvier":
                day = "2"
            elif waste_type == "Poubelle grise" and day == "1" and month == "avril":
                day = "2"
            elif waste_type == "Poubelle grise" and day == "20" and month == "mai":
                day = "21"
            elif waste_type == "Poubelle jaune" and day == "4" and month == "janvier":
                day = "5"
            elif waste_type == "Poubelle jaune" and day == "9" and month == "mai":
                day = "10"
            elif waste_type == "Poubelle jaune" and day == "23" and month == "mai":
                day = "24"
            elif waste_type == "Poubelle jaune" and day == "15" and month == "août":
                day = "16"

            date_collection = now.replace(month=MONTH_NAMES.index(month), day=int(day)).date()
            if date_collection < now.date():
                date_collection = date_collection.replace(year=date_collection.year + 1)

            entries = [
                Collection(
                    date=date_collection,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            ]  # List that holds collection schedule

            return entries
        else:
            return []
