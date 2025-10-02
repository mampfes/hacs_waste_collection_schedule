from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Taranto (araccolta.it)"
DESCRIPTION = "Source for Taranto (araccolta.it)."
URL = "https://araccolta.it/"
TEST_CASES = {
    "lama-san-vito-talsano Domestic": {
        "district": "lama-san-vito-talsano",
    },
    "isola-amministrativa non Domestic": {
        "district": "isola-amministrativa",
        "domestic": False,
    },
}


PARAM_TRANSLATIONS = {
    "en": {"district": "District", "domestic": "Domestic"},
    "it": {"district": "Quartiere", "domestic": "Utenze domestiche"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit [https://araccolta.it/#calendario](https://araccolta.it/#calendario) and select your district (Quartiere) write the argument exactly like in the URL after clicking on your district.",
    "it": "Visita [https://araccolta.it/#calendario](https://araccolta.it/#calendario) e seleziona il tuo quartiere, scrivi l'argomento esattamente come nell'URL dopo aver cliccato sul tuo quartiere.",
}

ICON_MAP = {
    "Carta e cartone": "mdi:newspaper",
    "Organico": "mdi:leaf",
    "Secco residuo": "mdi:delete",
    "Vetro": "mdi:bottle-wine",
    "Plastica e metalli": "mdi:bottle-soda-classic",
}


ITALIAN_WEEKDAYS = [
    "lunedì",
    "martedì",
    "mercoledì",
    "giovedì",
    "venerdì",
    "sabato",
    "domenica",
]

API_URL = "https://araccolta.it/{district}/"


class Source:
    def __init__(self, district: str, domestic: bool = True):
        self._district: str = district.lower().strip().replace(" ", "-")
        self._domestic: bool = domestic

    def fetch(self) -> list[Collection]:
        # get json file
        r = requests.get(API_URL.format(district=self._district))
        r.raise_for_status()

        section_id = "ud" if self._domestic else "und"

        soup = BeautifulSoup(r.text, "html.parser")

        section = soup.select_one(f"section#{section_id}")
        if not section:
            raise ValueError("could not find calendar section for district")

        entries: list[Collection] = []
        for card in section.select("div.calendar-card"):
            weekdays = (
                card.select_one("div.day-wrapper").text.strip().lower().split("/")
            )
            if len(weekdays) == 1:
                weekdays = weekdays[0].split(" - ")
            waste_types = (t.text for t in card.select("h3"))
            for weekday in weekdays:
                weekday_int = ITALIAN_WEEKDAYS.index(weekday)
                next_date = (
                    datetime.now()
                    + timedelta(days=(weekday_int - datetime.now().weekday()) % 7)
                ).date()
                for waste_type in waste_types:
                    entries += [
                        Collection(
                            date=next_date + timedelta(weeks=i),
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                        for i in range(25)
                    ]

        return entries
