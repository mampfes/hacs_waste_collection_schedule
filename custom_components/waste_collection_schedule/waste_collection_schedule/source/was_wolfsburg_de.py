import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wolfsburger Abfallwirtschaft und Straßenreinigung"
DESCRIPTION = "Source for waste collections for WAS-Wolfsburg, Germany."
URL = "https://was-wolfsburg.de"
TEST_CASES = {
    "Barnstorf": {"street": "Bahnhofspassage", "number": 1},
    "Sülfeld": {"street": "Bärheide", "number": 1},
}

ICON_MAP = {
    "Wertstofftonne": "mdi:recycle",
    "Bioabfall": "mdi:leaf",
    "Restabfall": "mdi:trash-can",
    "Altpapier": "mdi:file-document-outline",
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "number": "Hausnummer",
    }
}


class Source:
    def __init__(self, street: str | None, number: int | None):
        self._street = street
        self._number = str(number)

        if street is None:
            raise ValueError("Street must be set")
        if number is None:
            raise ValueError("Number must be set")

    def fetch(self) -> list[Collection]:
        # get token
        js = requests.get("https://abfuhrtermine.waswob.de/js/main.js")
        token = re.search(r"token=([^\"\n\`]*)", js.text)
        if token is None:
            raise ValueError("Token not found")

        entries = []
        r = requests.get(
            "https://apiabfuhrtermine.waswob.de/api/download-json",
            {
                "strasse": self._street,
                "hausnummer": self._number,
                "token": token.group(1),
            },
        )
        answer = r.json()

        for name, icon in ICON_MAP.items():
            for a in answer[0][name]:
                entries.append(
                    Collection(
                        date=datetime.strptime(a, "%Y-%m-%d").date(),
                        t=name,
                        icon=icon,
                    )
                )

        return entries
