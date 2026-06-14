from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES

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
    "Schadstoffsammlung": Icons.HAZARDOUS,
    "Abfuhr Weihnachtsbäume": Icons.CHRISTMAS_TREE,
}

PARAM_TRANSLATIONS: dict = {}
PARAM_DESCRIPTIONS: dict = {}


class Source:
    def __init__(self, strasse: str):
        self._strasse = strasse
        self._sitepark = SiteparkIES(
            API_URL, download_params={"kat": "1", "alarm": "0"}
        )

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse)
        return [
            Collection(date, waste_type, ICON_MAP.get(waste_type, Icons.GENERAL_WASTE))
            for date, waste_type in dates
        ]
