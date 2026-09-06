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
        )
        r.raise_for_status()
        answer = r.json()

        # As of early September 2026 the API wraps the collection dates in a
        # "behaelter" (container) dict keyed by container size, instead of
        # returning a flat list as the top-level element. See
        # https://github.com/mampfes/hacs_waste_collection_schedule/issues/7076
        if not isinstance(answer, dict) or not answer:
            raise ValueError(f"No data found for '{self._street} {self._number}'")

        entry = next(iter(answer.values()))
        behaelter = entry.get("behaelter", {})

        for container in behaelter.values():
            for name, icon in ICON_MAP.items():
                for date_str in container.get(name, {}):
                    entries.append(
                        Collection(
                            date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                            t=name,
                            icon=icon,
                        )
                    )

        return entries
