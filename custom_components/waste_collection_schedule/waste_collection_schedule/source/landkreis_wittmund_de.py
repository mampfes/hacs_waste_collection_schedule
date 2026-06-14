from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SiteparkIES import SiteparkIES

TITLE = "Landkreis Wittmund"
DESCRIPTION = "Source for Landkreis Wittmund waste collection."
URL = "https://www.landkreis-wittmund.de"
COUNTRY = "de"
TEST_CASES = {
    "CityWithoutStreet": {
        "ort": "Werdum",
    },
    "CityWithStreet": {
        "ort": "Werdum",
        "strasse": "alle Straßen",
    },
    # legacy parameter names must keep working
    "Legacy city/street": {
        "city": "Werdum",
        "street": "alle Straßen",
    },
}

API_URL = "https://www.landkreis-wittmund.de/Leben-Wohnen/Wohnen/Abfall/Abfuhrkalender/"
DOWNLOAD_PARAMS = {
    "ArtID[0]": "3105.1",
    "ArtID[1]": "1.4",
    "ArtID[2]": "1.2",
    "ArtID[3]": "1.3",
    "ArtID[4]": "1.1",
    "alarm": "0",
}


PARAM_TRANSLATIONS = {
    "de": {
        "ort": "Ort",
        "strasse": "Straße",
    }
}


class Source:
    def __init__(self, ort=None, strasse=None, city=None, street=None):
        # ``city`` / ``street`` are the legacy parameter names.
        self._ort = ort or city
        self._strasse = strasse or street
        self._sitepark = SiteparkIES(URL, download_params=DOWNLOAD_PARAMS)

    def fetch(self):
        refid = self._sitepark.resolve_refid(self._ort, API_URL)
        pois = self._sitepark.get_pois(strasse=self._strasse, refid=refid)
        dates = self._sitepark.fetch_ics(pois)
        return [Collection(date, waste_type) for date, waste_type in dates]
