from datetime import date, datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wolfsburger Abfallwirtschaft und Straßenreinigung"
DESCRIPTION = "Source for waste collections for WAS-Wolfsburg, Germany."
URL = "https://was-wolfsburg.de"
TEST_CASES = {
    "Barnstorf": {"street": "Bahnhofspassage"},
    "Sülfeld": {"street": "Bärheide"},
}

ICON_MAP = {
    "gelber Sack": "mdi:recycle",
    "Bioabfall": "mdi:leaf",
    "Restabfall": "mdi:trash-can",
    "Altpapier": "mdi:file-document-outline",
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
    }
}


class Source:
    def __init__(self, street: str | None):
        self._street = street
        if street is None:
            raise ValueError("Street must be set")

    def fetch(self) -> list[Collection]:
        entries = []
        r = requests.get(
            "https://abfuhrtermine.waswob.de/php/abfuhrtermineeingabe.php",
            {"k": self._street}
        )
        answer = r.json()

        for a in answer:
            entries.append(
                Collection(
                    date = datetime.strptime(a['date'], "%d.%m.%Y").date(),
                    t = a['waste'],
                    icon=ICON_MAP.get(a['waste'])
                )
            )

        return entries
