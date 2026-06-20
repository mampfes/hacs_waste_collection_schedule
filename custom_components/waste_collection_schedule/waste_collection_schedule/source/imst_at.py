from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Imst"
DESCRIPTION = "Waste collection schedule for Stadtgemeinde Imst, Austria."
URL = "https://www.imst.gv.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES = {
    "Auf Arzill 154": {
        "strasse": "Auf Arzill",
        "hausnummer": "154",
    },
    "Adlerweg 2": {
        "strasse": "Adlerweg",
        "hausnummer": "2",
    },
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.ORGANIC,
    "Gelbe Säcke": Icons.PLASTIC_PACKAGING,
    "Altpapier": Icons.PAPER,
    "Sperrmüll": Icons.BULKY,
    "Problemstoff": Icons.HAZARDOUS,
    "Altglas": Icons.GLASS,
    "Grünschnitt": Icons.GARDEN,
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
        "strasse": "Street name as listed in the Imst waste calendar dropdown.",
        "hausnummer": "House number as listed in the Imst waste calendar dropdown.",
    },
    "de": {
        "strasse": "Straßenname wie in der Abfallkalender-Auswahl von Imst aufgeführt.",
        "hausnummer": "Hausnummer wie in der Abfallkalender-Auswahl von Imst aufgeführt.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.imst.gv.at/Muellabfuhrplaene_1, pick your street and "
        "house number from the dropdowns, and use the same values for "
        "'strasse' and 'hausnummer'."
    ),
    "de": (
        "Öffnen Sie https://www.imst.gv.at/Muellabfuhrplaene_1, wählen Sie Ihre "
        "Straße und Hausnummer aus den Dropdown-Menüs, und verwenden Sie "
        "dieselben Werte für 'strasse' und 'hausnummer'."
    ),
}

_MENUONR = "222722602"


class Source(RiSKommunalSource):
    BASE_URL = "https://www.imst.gv.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = "https://www.imst.gv.at/Muellabfuhrplaene_1"
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "sprache": "1",
        "menuonr": _MENUONR,
    }

    def __init__(self, strasse: str, hausnummer: str | int):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
