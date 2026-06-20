from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Stadtbetriebe Steyr GmbH"
DESCRIPTION = "Source for Stadtbetriebe Steyr GmbH waste collection schedule."
URL = "https://www.steyr.at"
COUNTRY = "at"

SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES = {
    "Wolfernstraße 7": {
        "strasse": "Wolfernstraße",
        "hausnummer": "7",
    },
    "Aichetgasse 1": {
        "strasse": "Aichetgasse",
        "hausnummer": "1",
    },
}

ICON_MAP = {
    "Restabfall": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.ORGANIC,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Altglas": Icons.GLASS,
    "Problemstoff": Icons.HAZARDOUS,
    "Sperrmüll": Icons.BULKY,
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
        "strasse": "Street name as listed in the Steyr waste calendar.",
        "hausnummer": "House number as listed in the Steyr waste calendar.",
    },
    "de": {
        "strasse": "Straßenname wie im Steyrer Abfallkalender aufgelistet.",
        "hausnummer": "Hausnummer wie im Steyrer Abfallkalender aufgelistet.",
    },
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.steyr.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = (
        "https://www.steyr.at/system/web/kalender.aspx?sprache=1&menuonr=227376864"
    )
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "sprache": "1",
        "menuonr": "227376864",
    }

    def __init__(self, strasse: str, hausnummer: str | int):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
