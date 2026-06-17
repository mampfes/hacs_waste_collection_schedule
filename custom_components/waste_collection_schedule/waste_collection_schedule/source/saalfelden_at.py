from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Saalfelden am Steinernen Meer"
DESCRIPTION = "Source for Saalfelden am Steinernen Meer waste collection."
URL = "https://www.saalfelden.at"
COUNTRY = "at"

TEST_CASES = {
    "Achenweg 1": {"strasse": "Achenweg", "hausnummer": 1},
    "Abdeckerweg 5": {"strasse": "Abdeckerweg", "hausnummer": "5"},
    "Achenweg 4a": {"strasse": "Achenweg", "hausnummer": "4a"},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.BIO_KITCHEN,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Altpapier": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Sperrmüll": Icons.BULKY,
    "Christbaum": Icons.CHRISTMAS_TREE,
    "Weihnachtsbaum": Icons.CHRISTMAS_TREE,
    "Problemstoff": Icons.HAZARDOUS,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "strasse": "Street name as listed in the Saalfelden waste calendar.",
        "hausnummer": "House number as listed in the Saalfelden waste calendar.",
    },
    "de": {
        "strasse": "Straßenname wie im Saalfeldener Abfallkalender aufgelistet.",
        "hausnummer": "Hausnummer wie im Saalfeldener Abfallkalender aufgelistet.",
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
        "Visit https://www.saalfelden.at/Buergerservice/Abfallkalender, pick "
        "your street and house number from the dropdowns, and use the same "
        "values here."
    ),
    "de": (
        "Öffnen Sie https://www.saalfelden.at/Buergerservice/Abfallkalender, "
        "wählen Sie Ihre Straße und Hausnummer aus, und verwenden Sie dieselben "
        "Werte hier."
    ),
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.saalfelden.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = "https://www.saalfelden.at/Buergerservice/Abfallkalender"
    LOOKAHEAD_DAYS = 365
    MAX_PAGES = 30
    QUERY_PARAMS = {
        "detailonr": "225697049",
        "menuonr": "225696673",
    }

    def __init__(self, strasse, hausnummer):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
