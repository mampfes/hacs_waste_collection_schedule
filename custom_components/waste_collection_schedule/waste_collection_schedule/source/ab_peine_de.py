from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES

TITLE = "Landkreis Peine"
DESCRIPTION = "Source for Abfallwirtschaftsbetrieb Landkreis Peine waste collection."
URL = "https://ab-peine.de"
COUNTRY = "de"
TEST_CASES = {
    "Gerhart-Hauptmann-Straße (Peine-Kernstadt)": {
        "strasse": "Gerhart-Hauptmann-Straße",
    },
    "Adlerstraße (Peine-Kernstadt)": {"strasse": "Adlerstraße"},
}

API_URL = "https://www.ab-peine.de"

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
        self._sitepark = SiteparkIES(API_URL)

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse, ort=self._ort)
        return [Collection(date, waste_type) for date, waste_type in dates]
