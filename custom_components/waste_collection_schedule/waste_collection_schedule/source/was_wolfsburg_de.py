from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Wolfsburger Abfallwirtschaft und Straßenreinigung"
DESCRIPTION = "Source for waste collections for WAS-Wolfsburg, Germany."
URL = "https://was-wolfsburg.de"
TEST_CASES = {
    "Barnstorf": {"street": "Bahnhofspassage", "number": 1},
    "Sülfeld": {"street": "Bärheide", "number": 1},
}

ICON_MAP = {
    "Wertstofftonne": Icons.RECYCLING,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Restabfall": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
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
        entries = []
        r = requests.get(
            "https://abfuhrtermine.waswob.de/php/abfuhr_api.php",
            params={
                "action": "termine",
                "strasse": self._street,
                "hausnummer": self._number,
            },
            timeout=30,
        )
        r.raise_for_status()
        answer = r.json()
        if not isinstance(answer, list) or len(answer) == 0:
            raise ValueError("No schedule returned")

        schedule = answer[0]

        for name, icon in ICON_MAP.items():
            dates = schedule.get(name, {})
            if isinstance(dates, dict):
                raw_dates = dates.keys()
            elif isinstance(dates, list):
                raw_dates = dates
            else:
                continue
            for a in raw_dates:
                entries.append(
                    Collection(
                        date=datetime.strptime(a, "%Y-%m-%d").date(),
                        t=name,
                        icon=icon,
                    )
                )

        return entries
