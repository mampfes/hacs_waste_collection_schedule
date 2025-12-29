from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wolfsburger Abfallwirtschaft und Straßenreinigung"
DESCRIPTION = "Source for waste collections for WAS-Wolfsburg, Germany."
URL = "https://was-wolfsburg.de"
TEST_CASES = {
    "Barnstorf": {"street": "Bahnhofspassage", "house_number": "2"},
    "Sülfeld": {"street": "Bärheide", "house_number": "1"},
}

TOKEN = "fLEybUshbK5c2UEt6w4qYs2VxxR4MDPs"

ICON_MAP = {
    "gelber Sack": "mdi:recycle",
    "Bioabfall": "mdi:leaf",
    "Restabfall": "mdi:trash-can",
    "Altpapier": "mdi:file-document-outline",
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
    }
}


class Source:
    def __init__(self, street: str | None, house_number: str | None):
        if not street or not house_number:
            raise ValueError("street and house_number must be set")

        self._street = street
        self._house_number = house_number

    def fetch(self) -> list[Collection]:
        r = requests.get(
            "https://apiabfuhrtermine.waswob.de/api/download-json",
            params={
                "token": TOKEN,
                "strasse": self._street,
                "hausnummer": self._house_number,
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )

        r.raise_for_status()
        data = r.json()

        if not data:
            return []

        entries: list[Collection] = []
        entry = data[0]

        for waste_type, dates in entry.items():
            if waste_type in ("strIndex", "strName", "ortsteil", "hausnummer"):
                continue

            if waste_type not in ICON_MAP:
                continue

            for date_str in dates.keys():
                entries.append(
                    Collection(
                        date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                        t=waste_type,
                        icon=ICON_MAP[waste_type],
                    )
                )

        return entries
