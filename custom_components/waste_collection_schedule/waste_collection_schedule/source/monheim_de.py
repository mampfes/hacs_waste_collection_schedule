from datetime import date

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Monheim am Rhein"
DESCRIPTION = (
    "Source for Monheim am Rhein waste collection (Stadt Monheim am Rhein, NRW)."
)
URL = "https://www.monheim.de"
COUNTRY = "de"

TEST_CASES = {
    "Marderstraße": {"street": "Marderstraße"},
    "Ackerweg": {"street": "Ackerweg"},
    "Rheinpromenade": {"street": "Rheinpromenade"},
}

PARAM_TRANSLATIONS = {
    "en": {"street": "Street"},
    "de": {"street": "Straße"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name as shown in the Monheim am Rhein waste calendar.",
    },
    "de": {
        "street": "Straßenname wie im digitalen Abfallkalender Monheim am Rhein angegeben.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Open https://www.monheim.de/leben-in-monheim/abfall-stadtreinigung/abfallkalender and pick your street; use the exact spelling shown there.",
    "de": "Öffnen Sie https://www.monheim.de/leben-in-monheim/abfall-stadtreinigung/abfallkalender und wählen Sie Ihre Straße; verwenden Sie die genaue Schreibweise.",
}

ICON_MAP = {
    "Wertstoffhof": Icons.RECYCLING,
    "Schadstoff Mobil": Icons.HAZARDOUS,
    "Grünabfälle": Icons.GARDEN,
    "zusätzliche Grünabgabe": Icons.GARDEN,
    "Spülung und Leerung der Biotonnen": Icons.BIO_KITCHEN,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Restmüll": Icons.GENERAL_WASTE,
    "Braune Tonne": Icons.BIO_KITCHEN,
    "Blaue Tonne": Icons.PAPER,
    "Spülung und Leerung der Restmülltonnen": Icons.GENERAL_WASTE,
}

GARBAGE_TYPE_MAP = {
    "0": "Spülung und Leerung der Restmülltonnen",
    "1": "Wertstoffhof",
    "2": "Schadstoff Mobil",
    "3": "Grünabfälle",
    "4": "Spülung und Leerung der Biotonnen",
    "5": "Gelber Sack",
    "6": "Restmüll",
    "7": "Braune Tonne",
    "8": "Blaue Tonne",
    "9": "zusätzliche Grünabgabe",
}

STREETS_URL = "https://www.monheim.de/?type=1106181"
DATES_URL = "https://www.monheim.de/?type=1106182"


class Source:
    def __init__(self, street: str):
        self._street = street

    def fetch(self) -> list[Collection]:
        r = requests.get(STREETS_URL, timeout=30)
        r.raise_for_status()
        streets = r.json().get("streets", [])

        match = next(
            (s for s in streets if s["streetname"].lower() == self._street.lower()),
            None,
        )
        if match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                [s["streetname"] for s in streets],
            )

        district = str(match["district"])

        r = requests.get(DATES_URL, timeout=30)
        r.raise_for_status()
        collectiondates = r.json().get("collectiondates", [])

        entries: list[Collection] = []
        for record in collectiondates:
            record_districts = [
                d.strip() for d in record.get("districts", "").split(",") if d.strip()
            ]
            # Empty districts means the record applies to all streets (e.g. Wertstoffhof)
            if record_districts and district not in record_districts:
                continue

            garbage_id = str(record.get("garbageTypes", ""))
            waste_type = GARBAGE_TYPE_MAP.get(garbage_id, garbage_id)

            try:
                collection_date = date.fromisoformat(record["dateOfCollection"])
            except (KeyError, ValueError):
                continue

            entries.append(
                Collection(
                    collection_date,
                    waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
