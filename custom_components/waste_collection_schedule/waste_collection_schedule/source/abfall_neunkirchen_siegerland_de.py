from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Neunkirchen Siegerland"
DESCRIPTION = "Source for 'Abfallkalender Neunkirchen Siegerland'."
URL = "https://www.neunkirchen-siegerland.de"
COUNTRY = "de"
AUTOCOMPLETE_URL = f"{URL}/output/autocomplete.php"
CALENDAR_URL = f"{URL}/output/options.php"
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
        self._ics = ICS()
        self._session = requests.Session(impersonate="chrome")

    def fetch(self):
        args = {
            "out": "json",
            "type": "abto",
            "select": "2",
            "refid": "3362.1",
            "term": self._strasse,
        }
        header = {"Referer": URL}
        r = self._session.get(
            AUTOCOMPLETE_URL,
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
            CALENDAR_URL,
            params=args,
            headers=header,
            timeout=30,
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        return [
            Collection(date, waste_type, ICON_MAP.get(waste_type, Icons.GENERAL_WASTE))
            for date, waste_type in dates
        ]
