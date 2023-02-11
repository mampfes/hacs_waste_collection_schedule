import datetime
from waste_collection_schedule import Collection
import requests


TITLE = "EAD Darmstadt" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for waste collection in Darmstadt ead.darmstadt.de"  # Describe your source
URL = "https://ead.darmstadt.de/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Stresemannstraße": {"street": "Stresemannstraße"},
    "Trondheimstraße": {"street": "Trondheimstraße"},
    "Mühltalstraße": {"street": "Mühltalstraße"},
    "Heinheimer Straße": {"street": "Heinheimer Straße 1-15, 2-16"},
    "Kleyerstraße": {"street": "Kleyerstraße"},
    "Untere Mühlstraße": {"street": "Untere Mühlstraße 1-29, 2-36"},

}

API_URL = "https://ead.darmstadt.de/unser-angebot/privathaushalte/abfallkalender/singleStreet/"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "RM1": "mdi:trash-can",
    "RM2": "mdi:trash-can",
    "RM4": "mdi:trash-can",
    "WET": "mdi:recycle",
    "BIO": "mdi:leaf",
    "PPK": "mdi:package-variant",
}

TRASH_TYPES_NAME = {
    "RM1": "Restabfall (jede Woche, Schwarz)",
    "RM2": "Restabfall (Alle zwei Wochen, Orange)",
    "RM4": "Restabfall (Alle vier Wochen, Rot)",
    "WET": "Wertstoffe (Gelb)",
    "BIO": "Bioabfall (Braun)",
    "PPK": "Altpapier (Grün)",
}

class Source:
    def __init__(self, street):  # argX correspond to the args dict in the source configuration
        self.street = street

    def fetch(self):

        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details

        params = {"type": "742394", "street": self.street}

        r = requests.get(
            API_URL, params=params
        )

        entries = []  # List that holds collection schedule

        entrie_dict = r.json()
        
        if entrie_dict is None or entrie_dict == []:
            return entries
        
        for date, waste_type_list in r.json().items():
            for waste_type in waste_type_list:
                entries.append(
                    Collection(
                        date = datetime.datetime.strptime(date, "%d.%m.%Y").date(),  # Collection date
                        t = TRASH_TYPES_NAME.get(waste_type),  # Collection type
                        icon = ICON_MAP.get(waste_type),  # Collection icon
                    )
                )

        return entries