from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Gemeinde Bürmoos"
DESCRIPTION = "Source for Gemeinde Bürmoos, Austria."
URL = "https://www.buermoos.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES: dict[str, dict] = {
    "Birkenstraße 76a": {
        "strasse": "Birkenstraße",
        "hausnummer": "76a",
    },
    "Almweg 2": {
        "strasse": "Almweg",
        "hausnummer": "2",
    },
}

ICON_MAP = {
    "Biomüllabfuhr": Icons.ORGANIC,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Altpapier": Icons.PAPER,
    "Restmüll": Icons.GENERAL_WASTE,
    "Sperrmüll": Icons.BULKY,
    "Altglas": Icons.GLASS,
    "Problemstoff": Icons.HAZARDOUS,
    "GELB": Icons.PLASTIC_PACKAGING,
    "WEIß": Icons.GENERAL_WASTE,
    "ROT": Icons.GENERAL_WASTE,
    "LVP": Icons.PLASTIC_PACKAGING,
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
        "strasse": "Street name as listed in the Bürmoos waste calendar dropdown.",
        "hausnummer": "House number as listed in the Bürmoos waste calendar dropdown.",
    },
    "de": {
        "strasse": "Straßenname wie in der Abfallkalender-Auswahl von Bürmoos aufgeführt.",
        "hausnummer": "Hausnummer wie in der Abfallkalender-Auswahl von Bürmoos aufgeführt.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.buermoos.at/Service/Aktuelles/Muellkalender, pick your "
        "street and house number from the dropdowns, and use the same values for "
        "'strasse' and 'hausnummer'."
    ),
    "de": (
        "Öffnen Sie https://www.buermoos.at/Service/Aktuelles/Muellkalender, wählen "
        "Sie Ihre Straße und Hausnummer aus den Dropdown-Menüs, und verwenden Sie "
        "dieselben Werte für 'strasse' und 'hausnummer'."
    ),
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.buermoos.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = "https://www.buermoos.at/Service/Aktuelles/Muellkalender"
    LOOKAHEAD_DAYS = 365
    MAX_PAGES = 30
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": "219233420",
    }

    def __init__(self, strasse: str, hausnummer: str | int):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
