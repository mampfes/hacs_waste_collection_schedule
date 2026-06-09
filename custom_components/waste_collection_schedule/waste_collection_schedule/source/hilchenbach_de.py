from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Stadt Hilchenbach"
DESCRIPTION = "Source for 'Abfallkalender Stadt Hilchenbach'."
URL = "https://www.hilchenbach.de"
COUNTRY = "de"
TEST_CASES = {
    "Dammstraße (Hilchenbach)": {"strasse": "Dammstr"},
    "Am Bühl (Allenbach)": {"strasse": "Am Bühl"},
}

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
    def __init__(self, strasse):
        self._strasse = strasse
        self._ics = ICS()
        self._session = requests.Session(impersonate="chrome")

    def fetch(self):
        args = {
            "out": "json",
            "type": "abto",
            "select": "2",
            "term": self._strasse,
        }
        header = {"Referer": URL}
        r = self._session.get(
            "https://hilchenbach.de/output/autocomplete.php",
            params=args,
            headers=header,
            timeout=30,
        )
        r.raise_for_status()

        ids = r.json()

        if not isinstance(ids, list):
            raise Exception("Unexpected autocomplete response")

        if not ids:
            raise SourceArgumentNotFound(f"No address found for '{self._strasse}'")

        if len(ids) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "strasse", self._strasse, [id[1] for id in ids]
            )

        args = {"ModID": 48, "call": "ical", "pois": ids[0][0], "kat": 1, "alarm": 0}
        r = self._session.get(
            "https://hilchenbach.de/output/options.php",
            params=args,
            headers=header,
            timeout=30,
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        return [
            Collection(date, waste_type, ICON_MAP.get(waste_type, "mdi:trash-can"))
            for date, waste_type in dates
        ]
