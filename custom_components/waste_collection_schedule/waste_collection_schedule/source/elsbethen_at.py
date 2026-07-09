from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Elsbethen"
DESCRIPTION = "Source for Elsbethen waste collection."
URL = "https://www.gde-elsbethen.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES = {
    "Überfuhrstraße 2": {"strasse": "Überfuhrstraße", "hausnummer": "2"},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.BIO_KITCHEN,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Altpapier": Icons.PAPER,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "strasse": "Street name as listed in the Elsbethen waste calendar.",
        "hausnummer": "House number as listed in the Elsbethen waste calendar.",
    },
    "de": {
        "strasse": "Straßenname wie im Elsbethener Abfallkalender aufgelistet.",
        "hausnummer": "Hausnummer wie im Elsbethener Abfallkalender aufgelistet.",
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
        "Visit https://www.gde-elsbethen.at/Buergerservice/Abfall-Recycling/Abfallkalender, "
        "pick your street and house number from the dropdowns, and use the same values here."
    ),
    "de": (
        "Öffnen Sie https://www.gde-elsbethen.at/Buergerservice/Abfall-Recycling/Abfallkalender, "
        "wählen Sie Ihre Straße und Hausnummer aus, und verwenden Sie dieselben Werte hier."
    ),
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.gde-elsbethen.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = (
        "https://www.gde-elsbethen.at/system/web/kalender.aspx?menuonr=223627736"
    )
    LOOKAHEAD_DAYS = 365
    MAX_PAGES = 30
    QUERY_PARAMS: ClassVar = {
        "menuonr": "225141707",
    }

    def __init__(self, strasse, hausnummer):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
