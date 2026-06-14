from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES

TITLE = "Ostprignitz-Ruppin"
DESCRIPTION = "Source for Ostprignitz-Ruppin waste collection."
URL = "https://www.ostprignitz-ruppin.de"
COUNTRY = "de"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street as `strasse`. If the street name exists in several places, add the place name as `ort` to disambiguate.",
    "de": "Geben Sie Ihre Straße als `strasse` ein. Kommt der Straßenname in mehreren Orten vor, geben Sie zusätzlich den Ort als `ort` an.",
}

TEST_CASES = {
    "Am alten Gymnasium (Neuruppin)": {
        "ort": "Neuruppin",
        "strasse": "Am alten Gymnasium",
    },
    # legacy parameter names must keep working
    "Legacy: location/street": {
        "location": "Neuruppin",
        "street": "Bahnhofstraße",
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
    def __init__(self, strasse=None, ort=None, street=None, location=None):
        # ``street`` / ``location`` are the legacy parameter names.
        self._strasse = strasse or street
        self._ort = ort or location
        self._sitepark = SiteparkIES(URL, download_params={"monat": "", "alarm": "0"})

    def fetch(self):
        dates = self._sitepark.fetch(strasse=self._strasse, ort=self._ort)
        return [Collection(date, waste_type) for date, waste_type in dates]
