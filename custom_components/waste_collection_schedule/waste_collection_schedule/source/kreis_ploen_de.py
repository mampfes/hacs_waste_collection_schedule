from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES, match_icon

TITLE = "Abfallwirtschaft Kreis Plön"
DESCRIPTION = "Source for Abfallwirtschaft Kreis Plön waste collection."
URL = "https://www.kreis-ploen.de"
COUNTRY = "de"
TEST_CASES = {
    "Hauptstraße (Köhn)": {"strasse": "Hauptstraße", "ort": "Köhn"},
    "Achterhof (Martensrade)": {"strasse": "Achterhof", "ort": "Martensrade"},
}

ICON_MAP = {
    "Bioabfall": Icons.BIO_KITCHEN,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Papier": Icons.PAPER,
    "Restabfall": Icons.GENERAL_WASTE,
}

PARAM_TRANSLATIONS = {
    "de": {
        "strasse": "Straße",
        "ort": "Ort",
    },
    "en": {
        "strasse": "Street",
        "ort": "Place",
    },
}


class Source:
    def __init__(self, strasse, ort=None):
        self._strasse = strasse
        self._ort = ort
        self._sitepark = SiteparkIES(URL)

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse, ort=self._ort)
        return [
            Collection(date, waste_type, match_icon(waste_type, ICON_MAP))
            for date, waste_type in dates
        ]
