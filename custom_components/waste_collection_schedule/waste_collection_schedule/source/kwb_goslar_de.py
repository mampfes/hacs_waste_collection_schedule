from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.SiteparkIES import SiteparkIES, match_icon

TITLE = "Kreiswirtschaftsbetriebe Goslar"
DESCRIPTION = "Source for kwb-goslar.de waste collection."
URL = "https://www.kwb-goslar.de"
COUNTRY = "de"
TEST_CASES = {
    "Berliner Straße (Clausthal-Zellerfeld)": {"pois": "2523.602"},
    "Braunschweiger Straße (Seesen)": {"pois": "2523.409"},
    "Marktstraße (Seesen)": {"strasse": "Marktstraße", "ort": "Seesen"},
}

ICON_MAP = {
    "Baum- und Strauchschnitt": Icons.ORGANIC,
    "Biotonne": Icons.BIO_KITCHEN,
    "Blaue Tonne": Icons.NEWSPAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Restmülltonne": Icons.GENERAL_WASTE,
    "Weihnachtsbäume": Icons.CHRISTMAS_TREE,
}


PARAM_TRANSLATIONS = {
    "de": {
        "strasse": "Straße",
        "ort": "Ort",
        "pois": "POIS",
    },
    "en": {
        "strasse": "Street",
        "ort": "Place",
        "pois": "POIS",
    },
}

PARAM_DESCRIPTIONS = {
    "de": {
        "strasse": "Straßenname (per Autocomplete aufgelöst).",
        "ort": "Optionaler Ort/Ortsteil zur Eindeutigkeit (z.B. 'Seesen').",
        "pois": "Direkte POIS-ID (Alternative zur Straßeneingabe).",
    },
    "en": {
        "strasse": "Street name (resolved via autocomplete).",
        "ort": "Optional place/district to disambiguate (e.g. 'Seesen').",
        "pois": "Direct POIS id (alternative to entering a street).",
    },
}


class Source:
    def __init__(self, strasse=None, ort=None, pois=None):
        self._strasse = strasse
        self._ort = ort
        self._pois = pois
        self._sitepark = SiteparkIES(URL)

    def fetch(self):
        dates = self._sitepark.fetch(
            strasse=self._strasse, ort=self._ort, pois=self._pois
        )
        return [
            Collection(date=date, t=waste_type, icon=match_icon(waste_type, ICON_MAP))
            for date, waste_type in dates
        ]
