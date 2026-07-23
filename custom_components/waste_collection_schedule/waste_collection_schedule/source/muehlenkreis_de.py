from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES, match_icon

TITLE = "Mühlenkreis Minden-Lübbecke"
DESCRIPTION = "Source for Mühlenkreis Minden-Lübbecke waste collection."
URL = "https://www.muehlenkreis.de"
COUNTRY = "de"
TEST_CASES = {
    "Hauptstraße (Harlinghausen)": {"strasse": "Hauptstraße", "ort": "Harlinghausen"},
    "Berliner Straße (Bad Holzhausen)": {
        "strasse": "Berliner Straße",
        "ort": "Bad Holzhausen",
    },
}
SOURCE_CODEOWNERS = ["@bbr111"]

ICON_MAP = {
    "Biotonne": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "Restmüll": Icons.GENERAL_WASTE,
    "Gelbe": Icons.PLASTIC_PACKAGING,
    "Schadstoff": Icons.HAZARDOUS,
    "Sperrmüll": Icons.BULKY,
    "Weihnachtsbaum": Icons.CHRISTMAS_TREE,
    "Grünschnitt": Icons.GARDEN,
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

PARAM_DESCRIPTIONS = {
    "de": {
        "strasse": "Straßenname oder eindeutiger Teil davon.",
        "ort": "Optionaler Ort zur Eindeutigkeit (der Teil in Klammern, z.B. 'Harlinghausen').",
    },
    "en": {
        "strasse": "Street name or a unique part of it.",
        "ort": "Optional place to disambiguate (the part in parentheses, e.g. 'Harlinghausen').",
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
