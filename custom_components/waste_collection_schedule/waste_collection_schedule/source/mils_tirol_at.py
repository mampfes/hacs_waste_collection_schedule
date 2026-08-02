from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Gemeinde Mils"
DESCRIPTION = "Source for Gemeinde Mils, Tyrol, Austria."
URL = "https://mils-tirol.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES: dict[str, dict] = {
    "Fichtenweg 21": {
        "strasse": "Fichtenweg",
        "hausnummer": "21",
    },
    "Dorfplatz 1": {
        "strasse": "Dorfplatz",
        "hausnummer": "1",
    },
}

ICON_MAP = {
    "Biomüll": Icons.ORGANIC,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Restmüll": Icons.GENERAL_WASTE,
    "Altpapier&Kleinkartons": Icons.PAPER,
    "Problemstoffsammlung": Icons.HAZARDOUS,
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
        "strasse": "Street name as listed in the Mils waste calendar dropdown.",
        "hausnummer": "House number as listed in the Mils waste calendar dropdown.",
    },
    "de": {
        "strasse": "Straßenname wie in der Abfallkalender-Auswahl von Mils aufgeführt.",
        "hausnummer": "Hausnummer wie in der Abfallkalender-Auswahl von Mils aufgeführt.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://mils-tirol.at/Service/Dienstleistungen/Abfallkalender, pick "
        "your street and house number from the dropdowns, and use the same values "
        "for 'strasse' and 'hausnummer'."
    ),
    "de": (
        "Öffnen Sie https://mils-tirol.at/Service/Dienstleistungen/Abfallkalender, "
        "wählen Sie Ihre Straße und Hausnummer aus den Dropdown-Menüs, und "
        "verwenden Sie dieselben Werte für 'strasse' und 'hausnummer'."
    ),
}


class Source(RiSKommunalSource):
    BASE_URL = "https://mils-tirol.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = "https://mils-tirol.at/Service/Dienstleistungen/Abfallkalender"
    LOOKAHEAD_DAYS = 365
    MAX_PAGES = 30
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": "226285523",
    }

    def __init__(self, strasse: str, hausnummer: str | int):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
