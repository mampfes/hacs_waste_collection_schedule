from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES

TITLE = "Neunkirchen Siegerland"
DESCRIPTION = "Source for 'Abfallkalender Neunkirchen Siegerland'."
URL = "https://www.neunkirchen-siegerland.de"
COUNTRY = "de"
REFID = "3362.1"
TEST_CASES = {"Waldstraße": {"strasse": "Waldstr"}}
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
    },
    "de": {
        "strasse": "Straße",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "strasse": "Partial or full street name as shown on the Neunkirchen Siegerland waste calendar (e.g. 'Waldstr' for 'Waldstraße').",
    },
    "de": {
        "strasse": "Teil- oder vollständiger Straßenname wie im Abfallkalender Neunkirchen Siegerland (z.B. 'Waldstr' für 'Waldstraße').",
    },
}


class Source:
    def __init__(self, strasse):
        self._strasse = strasse
        self._sitepark = SiteparkIES(
            URL, refid=REFID, download_params={"kat": "1", "alarm": "0"}
        )

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse)
        return [
            Collection(date, waste_type, ICON_MAP.get(waste_type, Icons.GENERAL_WASTE))
            for date, waste_type in dates
        ]
