from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES, match_icon

TITLE = "Stadt Hilchenbach"
DESCRIPTION = "Source for 'Abfallkalender Stadt Hilchenbach'."
URL = "https://www.hilchenbach.de"
COUNTRY = "de"
TEST_CASES = {
    "Dammstraße (Hilchenbach)": {"strasse": "Dammstr"},
    "Am Bühl (Allenbach)": {"strasse": "Am Bühl"},
}

API_URL = "https://hilchenbach.de"

ICON_MAP = {
    "Biomüll": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "Restmüll": Icons.GENERAL_WASTE,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Astschnitt": Icons.GARDEN,
    "Schadstoff": Icons.HAZARDOUS,
    "Weihnachtsbäume": Icons.CHRISTMAS_TREE,
}

PARAM_TRANSLATIONS = {
    "de": {
        "strasse": "Straße",
        "ort": "Ortsteil",
    },
    "en": {
        "strasse": "Street",
        "ort": "District",
    },
}
PARAM_DESCRIPTIONS = {
    "de": {
        "strasse": "Straßenname oder eindeutiger Teil davon.",
        "ort": "Optionaler Ortsteil zur Eindeutigkeit (der Teil in Klammern, z.B. 'Allenbach').",
    },
    "en": {
        "strasse": "Street name or a unique part of it.",
        "ort": "Optional district to disambiguate (the part in parentheses, e.g. 'Allenbach').",
    },
}


class Source:
    def __init__(self, strasse: str, ort=None):
        self._strasse = strasse
        self._ort = ort
        self._sitepark = SiteparkIES(
            API_URL, download_params={"kat": "1", "alarm": "0"}
        )

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse, ort=self._ort)
        return [
            Collection(date, waste_type, match_icon(waste_type, ICON_MAP))
            for date, waste_type in dates
        ]
