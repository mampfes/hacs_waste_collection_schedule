from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES, match_icon

TITLE = "Kreisstadt Groß-Gerau"
DESCRIPTION = "Source for Kreisstadt Groß-Gerau waste collection."
URL = "https://www.gross-gerau.de"
COUNTRY = "de"
REFID = "3411.1"

ICON_MAP = {
    "Bio": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "Gelb": Icons.PLASTIC_PACKAGING,
    "Wertstoff": Icons.RECYCLING,
    "Sperrmüll": Icons.BULKY,
    "Rest": Icons.GENERAL_WASTE,
}
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
        return [
            Collection(date, waste_type, match_icon(waste_type, ICON_MAP))
            for date, waste_type in dates
        ]
