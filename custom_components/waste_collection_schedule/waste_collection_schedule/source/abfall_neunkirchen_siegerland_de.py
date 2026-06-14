from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES

TITLE = "Neunkirchen Siegerland"
DESCRIPTION = "Source for 'Abfallkalender Neunkirchen Siegerland'."
URL = "https://www.neunkirchen-siegerland.de"
COUNTRY = "de"
REFID = "3362.1"
TEST_CASES = {
    "Waldstraße": {"strasse": "Waldstr"},
    "Altenseelbacher Weg (Neunkirchen)": {
        "strasse": "Altenseelbacher Weg",
        "ort": "Neunkirchen",
    },
}
SOURCE_CODEOWNERS = ["@bbr111"]

ICON_MAP = {
    "Biotonne": Icons.BIO_KITCHEN,
    "Papiertonne / Papiercontainer": Icons.PAPER,
    "Restmülltonne": Icons.GENERAL_WASTE,
    "Spartonne Restmüll": Icons.GENERAL_WASTE,
    "Container Restmüll": Icons.GENERAL_WASTE,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Astschnittsammlung": Icons.GARDEN,
    "Schadstoffsammlung": Icons.HAZARDOUS,
}

PARAM_TRANSLATIONS = {
    "en": {
        "strasse": "Street",
        "ort": "District",
    },
    "de": {
        "strasse": "Straße",
        "ort": "Ortsteil",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "strasse": "Partial or full street name as shown on the Neunkirchen Siegerland waste calendar (e.g. 'Waldstr' for 'Waldstraße').",
        "ort": "Optional district (Ortsteil) to disambiguate a street that exists in several places, i.e. the part shown in parentheses (e.g. 'Neunkirchen').",
    },
    "de": {
        "strasse": "Teil- oder vollständiger Straßenname wie im Abfallkalender Neunkirchen Siegerland (z.B. 'Waldstr' für 'Waldstraße').",
        "ort": "Optionaler Ortsteil zur Eindeutigkeit, falls die Straße in mehreren Ortsteilen vorkommt, also der Teil in Klammern (z.B. 'Neunkirchen').",
    },
}


class Source:
    def __init__(self, strasse, ort=None):
        self._strasse = strasse
        self._ort = ort
        self._sitepark = SiteparkIES(
            URL, refid=REFID, download_params={"kat": "1", "alarm": "0"}
        )

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse, ort=self._ort)
        return [
            Collection(date, waste_type, ICON_MAP.get(waste_type, Icons.GENERAL_WASTE))
            for date, waste_type in dates
        ]
