from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Enns"
DESCRIPTION = "Waste collection schedule for Enns, Austria."
URL = "https://www.enns.at"
COUNTRY = "at"

TEST_CASES = {
    "Am Damm 1": {
        "strasse": "Am Damm",
        "hausnummer": "1",
    },
    "Donaustraße 1": {
        "strasse": "Donaustraße",
        "hausnummer": "1",
    },
}

SOURCE_CODEOWNERS = ["@bbr111"]

ICON_MAP = {
    "Bioabfall": Icons.ORGANIC,
    "Restabfall 2-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 4-wöchentlich": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
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
        "strasse": "Street name as listed in the Enns waste calendar.",
        "hausnummer": "House number as listed in the Enns waste calendar.",
    },
    "de": {
        "strasse": "Straßenname wie im Ennser Abfallkalender aufgelistet.",
        "hausnummer": "Hausnummer wie im Ennser Abfallkalender aufgelistet.",
    },
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.enns.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = (
        "https://www.enns.at/system/web/kalender.aspx?sprache=1&menuonr=227945554"
    )
    RAISE_ON_EMPTY = True
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": "227945554",
    }

    def __init__(self, strasse, hausnummer):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
