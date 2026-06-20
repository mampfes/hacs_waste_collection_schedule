from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Micheldorf in Oberösterreich"
DESCRIPTION = "Source for Micheldorf in Oberösterreich, Austria."
URL = "https://www.micheldorf.at"
COUNTRY = "at"

TEST_CASES = {
    "Adalbert-Stifter-Straße 1": {
        "strasse": "Adalbert-Stifter-Straße",
        "hausnummer": "1",
    },
    "Alterpichlstraße 2": {
        "strasse": "Alterpichlstraße",
        "hausnummer": "2",
    },
}

ICON_MAP = {
    "Bioabfall": Icons.ORGANIC,
    "Restabfall 2-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 4-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 6-wöchentlich": Icons.GENERAL_WASTE,
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
        "strasse": "Street name as listed in the Micheldorf waste calendar.",
        "hausnummer": "House number as listed in the Micheldorf waste calendar.",
    },
    "de": {
        "strasse": "Straßenname wie im Micheldorfer Abfallkalender aufgelistet.",
        "hausnummer": "Hausnummer wie im Micheldorfer Abfallkalender aufgelistet.",
    },
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.micheldorf.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = (
        "https://www.micheldorf.at/system/web/kalender.aspx?sprache=1&menuonr=227975509"
    )
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "sprache": "1",
        "menuonr": "227975509",
    }

    def __init__(self, strasse, hausnummer):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
