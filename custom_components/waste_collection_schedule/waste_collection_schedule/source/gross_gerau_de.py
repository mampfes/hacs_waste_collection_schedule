from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES

TITLE = "Kreisstadt Groß-Gerau"
DESCRIPTION = "Source for Kreisstadt Groß-Gerau waste collection."
URL = "https://www.gross-gerau.de"
COUNTRY = "de"
REFID = "3411.1"
TEST_CASES = {
    "Adam-Rauch-Straße (Groß-Gerau)": {
        "strasse": "Adam-Rauch-Straße",
        "ort": "Groß-Gerau",
    },
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
        self._sitepark = SiteparkIES(URL, refid=REFID)

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse, ort=self._ort)
        return [Collection(date, waste_type) for date, waste_type in dates]
