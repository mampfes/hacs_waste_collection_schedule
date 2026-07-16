from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Oberndorf bei Schwanenstadt"
DESCRIPTION = "Source for Oberndorf bei Schwanenstadt waste collection."
URL = "https://www.oberndorf.ooe.gv.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES = {
    "Am Hang 2": {"strasse": "Am Hang", "hausnummer": "2"},
    "Bergstraße 5": {"strasse": "Bergstraße", "hausnummer": "5"},
}

ICON_MAP = {
    "Restabfall": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Altpapier": Icons.PAPER,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "strasse": "Street name as listed in the Oberndorf bei Schwanenstadt waste calendar.",
        "hausnummer": "House number as listed in the Oberndorf bei Schwanenstadt waste calendar.",
    },
    "de": {
        "strasse": "Straßenname wie im Abfallkalender von Oberndorf bei Schwanenstadt aufgelistet.",
        "hausnummer": "Hausnummer wie im Abfallkalender von Oberndorf bei Schwanenstadt aufgelistet.",
    },
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

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://www.oberndorf.ooe.gv.at, pick your street and house number "
        "from the waste-calendar dropdowns on the homepage, and use the same values here."
    ),
    "de": (
        "Öffnen Sie https://www.oberndorf.ooe.gv.at, wählen Sie Ihre Straße und "
        "Hausnummer aus den Abfallkalender-Auswahlfeldern auf der Startseite, und "
        "verwenden Sie dieselben Werte hier."
    ),
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.oberndorf.ooe.gv.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = "https://www.oberndorf.ooe.gv.at"
    LOOKAHEAD_DAYS = 365
    MAX_PAGES = 30
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": "227435354",
    }

    def __init__(self, strasse: str, hausnummer: str | int):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
