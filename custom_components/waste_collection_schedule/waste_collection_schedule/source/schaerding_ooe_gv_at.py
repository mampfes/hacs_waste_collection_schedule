from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Schärding"
DESCRIPTION = "Source for Schärding, Austria."
URL = "https://www.schaerding.ooe.gv.at"
COUNTRY = "at"

TEST_CASES = {
    "Adalbert-Stifter-Straße 1": {
        "strasse": "Adalbert-Stifter-Straße",
        "hausnummer": "1",
    },
    "Aigerdinger Straße 2": {
        "strasse": "Aigerdinger Straße",
        "hausnummer": 2,
    },
}

ICON_MAP = {
    "Restabfall wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 2-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 4-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 6-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall": Icons.GENERAL_WASTE,
    "Restmüll": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Biomüll": Icons.BIO_KITCHEN,
    "Altpapier": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Sperrmüll": Icons.BULKY,
    "Altglas": Icons.GLASS,
    "Problemstoff": Icons.HAZARDOUS,
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
        "strasse": "Street name as listed in the Schärding waste calendar.",
        "hausnummer": "House number as listed in the Schärding waste calendar.",
    },
    "de": {
        "strasse": "Straßenname wie im Schärdinger Abfallkalender aufgelistet.",
        "hausnummer": "Hausnummer wie im Schärdinger Abfallkalender aufgelistet.",
    },
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.schaerding.ooe.gv.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = (
        "https://www.schaerding.ooe.gv.at/system/web/kalender.aspx?menuonr=226878372"
    )
    RAISE_ON_EMPTY = True
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": "226878372",
    }

    def __init__(self, strasse, hausnummer):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
