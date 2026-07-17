from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Puch bei Hallein"
DESCRIPTION = "Waste collection schedule for Puch bei Hallein, Austria."
URL = "https://www.puchbeihallein.gv.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@nerdoc"]

TEST_CASES: dict[str, dict] = {
    "Ahornstraße 3": {"strasse": "Ahornstraße", "hausnummer": "3"},
    "Austraße 2": {"strasse": "Austraße", "hausnummer": "2"},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.ORGANIC,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
}

PARAM_TRANSLATIONS = {
    "en": {
        "strasse": "Street",
        "hausnummer": "House number",
    },
    "de": {
        "strasse": "Straße",
        "hausnummer": "Hausnummer",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "strasse": "Street name as listed in the Puch bei Hallein waste calendar dropdown.",
        "hausnummer": "House number as listed in the Puch bei Hallein waste calendar dropdown (e.g. '3', '4a').",
    },
    "de": {
        "strasse": "Straßenname wie im Abfallkalender der Gemeinde Puch bei Hallein.",
        "hausnummer": "Hausnummer wie im Abfallkalender der Gemeinde Puch bei Hallein (z. B. '3', '4a').",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender, "
        "pick your street and house number from the dropdowns, and use the same values "
        "for 'strasse' and 'hausnummer'."
    ),
    "de": (
        "Öffnen Sie https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender, "
        "wählen Sie Ihre Straße und Hausnummer aus den Dropdown-Menüs, und verwenden Sie "
        "dieselben Werte für 'strasse' und 'hausnummer'."
    ),
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.puchbeihallein.gv.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = (
        "https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender"
    )
    LOOKAHEAD_DAYS = 365
    MAX_PAGES = 30
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": "226095231",
    }

    def __init__(self, strasse: str, hausnummer: str | int):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
