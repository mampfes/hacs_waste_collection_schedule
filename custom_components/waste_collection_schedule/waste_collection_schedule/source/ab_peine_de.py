from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES, match_icon

TITLE = "Landkreis Peine"
DESCRIPTION = "Source for Abfallwirtschaftsbetrieb Landkreis Peine waste collection."
URL = "https://ab-peine.de"
COUNTRY = "de"
TEST_CASES = {
    "Gerhart-Hauptmann-Straße (Peine-Kernstadt)": {
        "strasse": "Gerhart-Hauptmann-Straße",
    },
    "Adlerstraße (Peine-Kernstadt)": {"strasse": "Adlerstraße"},
    "Adlerstraße with municipality": {
        "strasse": "Adlerstraße",
        "ort": "Peine-Kernstadt (mit Telgte)",
    },
    "Osterriehe (Broistedt)": {
        "strasse": "Osterriehe",
        "ort": "Broistedt",
    },
    "Vechelde (Hauptort)": {
        "strasse": "alle Straßen",
        "ort": "Vechelde (Hauptort)",
    },
    "Wendeburg (Hauptort)": {
        "strasse": "alle Straßen",
        "ort": "Wendeburg (Hauptort)",
    },
}

API_URL = "https://www.ab-peine.de"

ICON_MAP = {
    "Altpapier": Icons.PAPER,
    "Biotonne": Icons.BIO_KITCHEN,
    "Gelbe Säcke": Icons.PLASTIC_PACKAGING,
    "Restmüll": Icons.GENERAL_WASTE,
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
        self._sitepark = SiteparkIES(API_URL)

    def fetch(self):
        refid = (
            self._sitepark.resolve_refid(self._ort, API_URL + "/Abfuhrtermine/")
            if self._ort
            else None
        )
        dates = self._sitepark.fetch(strasse=self._strasse, refid=refid)
        return [
            Collection(date, waste_type, match_icon(waste_type, ICON_MAP))
            for date, waste_type in dates
        ]
