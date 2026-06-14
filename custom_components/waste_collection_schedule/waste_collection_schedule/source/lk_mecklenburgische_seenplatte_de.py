from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES, match_icon

TITLE = "Landkreis Mecklenburgische Seenplatte"
DESCRIPTION = "Source for Landkreis Mecklenburgische Seenplatte waste collection."
URL = "https://www.lk-mecklenburgische-seenplatte.de"
COUNTRY = "de"
TEST_CASES = {
    "Atelierstraße (Neubrandenburg)": {
        "ort": "Neubrandenburg",
        "strasse": "Atelierstraße",
    },
    "Dargun": {"ort": "Dargun", "strasse": "Dargun"},
    # legacy parameter names must keep working
    "Ahornweg (Altentreptow) [legacy]": {"city": "Altentreptow", "street": "Ahornweg"},
}

ICON_MAP = {
    "Biotonne": Icons.BIO_KITCHEN,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Papiertonne": Icons.PAPER,
    "Restmüll": Icons.GENERAL_WASTE,
}

PARAM_TRANSLATIONS = {
    "de": {
        "ort": "Ort",
        "strasse": "Straße",
    },
    "en": {
        "ort": "City",
        "strasse": "Street",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "ort": "Optional municipality name to disambiguate streets that exist in several places.",
        "strasse": "Street or district name. For entries shown with parentheses (e.g. 'Dargun (Dargun)') use only the part before the parenthesis (e.g. 'Dargun').",
    },
    "de": {
        "ort": "Optionaler Gemeindename zur Eindeutigkeit, falls die Straße in mehreren Orten vorkommt.",
        "strasse": "Straßen- oder Ortsteilname. Bei Einträgen mit Klammern (z.B. 'Dargun (Dargun)') nur den Teil vor der Klammer verwenden (z.B. 'Dargun').",
    },
}


class Source:
    def __init__(self, strasse=None, ort=None, street=None, city=None):
        # ``street`` / ``city`` are the legacy parameter names.
        self._strasse = strasse or street
        self._ort = ort or city
        self._sitepark = SiteparkIES(URL)

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse, ort=self._ort)
        return [
            Collection(date, waste_type, match_icon(waste_type, ICON_MAP))
            for date, waste_type in dates
        ]
