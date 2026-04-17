import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Tonnenticker Pro"
DESCRIPTION = "Source for Tonnenticker Pro (RegioIT) waste collection schedules."
URL = "https://www.regioit.de"
COUNTRY = "de"

API_BASE = "https://krwaf-abfallapp.regioit.de/abfall-app-krwaf/rest"

TEST_CASES = {
    "Steinhagen - Waldbadstrasse": {
        "city": "Steinhagen",
        "street": "Waldbadstra\u00dfe (Bahnhofstr. bis Rote Erde)",
    },
    "Warendorf - Agnes-Miegel-Weg": {
        "city": "Warendorf",
        "street": "Agnes-Miegel-Weg",
    },
}

ICON_MAP = {
    "restabfall": "mdi:trash-can",
    "bioabfall": "mdi:leaf",
    "papiertonne": "mdi:recycle",
    "altpapier": "mdi:recycle",
    "gelbe tonne": "mdi:recycle",
    "gelber sack": "mdi:recycle",
    "sperr": "mdi:sofa",
    "schadstoff": "mdi:delete-alert",
    "wertstoff": "mdi:recycle",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Municipality name (e.g. 'Steinhagen', 'Warendorf')",
        "street": "Street name — use exact spelling from the provider's calendar",
    },
    "de": {
        "city": "Ortsname (z. B. 'Steinhagen', 'Warendorf')",
        "street": "Straßenname — genaue Schreibweise des Anbieters verwenden",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"city": "City", "street": "Street"},
    "de": {"city": "Ort", "street": "Straße"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your municipality, then use the exact street name shown in the Tonnenticker Pro app or the provider's website.",
    "de": "Wählen Sie Ihren Ort und verwenden Sie den genauen Straßennamen aus der Tonnenticker Pro App oder der Website des Anbieters.",
}


class Source:
    def __init__(self, city: str, street: str):
        self._city = city.strip()
        self._street = street.strip()

    def fetch(self) -> list[Collection]:
        orte = requests.get(f"{API_BASE}/orte", timeout=30).json()
        ort = next((o for o in orte if o["name"].lower() == self._city.lower()), None)
        if ort is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, [o["name"] for o in orte]
            )

        strassen = requests.get(
            f"{API_BASE}/orte/{ort['id']}/strassen", timeout=30
        ).json()
        strasse = next(
            (s for s in strassen if s["name"].lower() == self._street.lower()), None
        )
        if strasse is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, [s["name"] for s in strassen]
            )

        fraktionen = requests.get(
            f"{API_BASE}/strassen/{strasse['id']}/fraktionen", timeout=30
        ).json()
        fraktion_map = {f["id"]: f["name"] for f in fraktionen}

        termine = requests.get(
            f"{API_BASE}/strassen/{strasse['id']}/termine", timeout=30
        ).json()

        entries = []
        for termin in termine:
            date = datetime.date.fromisoformat(termin["datum"])
            fraktion_id = termin["bezirk"]["fraktionId"]
            waste_type = fraktion_map.get(fraktion_id, f"Fraktion {fraktion_id}")
            icon = next(
                (v for k, v in ICON_MAP.items() if k in waste_type.lower()),
                "mdi:trash-can",
            )
            entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
