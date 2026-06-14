from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES

TITLE = "Abfallwirtschaft Kreis Plön"
DESCRIPTION = "Source for Abfallwirtschaft Kreis Plön waste collection."
URL = "https://www.kreis-ploen.de"
COUNTRY = "de"
TEST_CASES = {
    "Hauptstraße (Köhn)": {"strasse": "Hauptstraße", "ort": "Köhn"},
    "Achterhof (Martensrade)": {"strasse": "Achterhof", "ort": "Martensrade"},
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
        return [Collection(date, waste_type) for date, waste_type in dates]
