import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import (
    Collection,  # type: ignore[attr-defined]
    Icons,
)
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "AWB Birkenfeld"
DESCRIPTION = (
    "Source for AWB Birkenfeld (Abfallwirtschaftsbetrieb Landkreis Birkenfeld), Germany"
)
URL = "https://www.awb-bir.de"
TEST_CASES = {
    "Reichenbach, Auf dem Schoß": {"street": "Auf dem Schoß", "city": "Reichenbach"},
    "Hahnweiler, Falkenweg": {"street": "Falkenweg", "city": "Hahnweiler"},
    "Horbruch, Im Kätz": {"street": "Im Kätz", "city": "Horbruch"},
    "unique street without city": {"street": "Auf dem Schoß"},
}

ICON_MAP = {
    "Restabfall": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Problemabfälle": Icons.HAZARDOUS,
}

API_URL = "https://www.awb-bir.de/Service/(0)Abfuhrkalender/"

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "city": "Ortsgemeinde",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name exactly as shown on the AWB Birkenfeld waste calendar page.",
        "city": "Ortsgemeinde (village/town). Only required if the street name occurs in more than one village.",
    },
    "de": {
        "street": "Straßenname genau wie im Abfuhrkalender der AWB Birkenfeld angegeben.",
        "city": "Ortsgemeinde. Nur erforderlich, wenn der Straßenname in mehreren Gemeinden vorkommt.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the AWB Birkenfeld waste calendar page and search for your street. Use the exact street name (and, if it "
    "occurs in more than one village, the Ortsgemeinde) as shown in the search results.",
    "de": "Besuchen Sie die Abfuhrkalender-Seite der AWB Birkenfeld und suchen Sie nach Ihrer Straße. Verwenden Sie den "
    "Straßennamen (und, falls dieser in mehreren Gemeinden vorkommt, die Ortsgemeinde) genau wie in den Suchergebnissen "
    "angezeigt.",
}


class Source:
    def __init__(self, street: str, city: str | None = None):
        self._street = street
        self._city = city

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL, timeout=30)
        r.raise_for_status()
        text = r.text

        def extract(varname: str) -> list:
            match = re.search(rf"var {varname} = (\[.*?\]);", text, re.DOTALL)
            if not match:
                raise ValueError(f"Could not find '{varname}' data on {API_URL}")
            return json.loads(match.group(1))

        streets = extract("tblStrassen")
        street_groups = extract("tblStrassenGruppen")
        dates = extract("tblTermine")
        waste_types = extract("tblMuellarten")

        street_lower = self._street.strip().lower()
        matches = [s for s in streets if s["Strasse"].strip().lower() == street_lower]

        if self._city:
            city_lower = self._city.strip().lower()
            matches = [
                s for s in matches if s["Gemeinde"].strip().lower() == city_lower
            ]

        if not matches:
            all_streets = sorted({s["Strasse"] for s in streets})
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, all_streets
            )

        cities = sorted({s["Gemeinde"] for s in matches})
        if len(cities) > 1:
            raise SourceArgAmbiguousWithSuggestions("city", self._city, cities)

        street_ids = {s["StrassenId"] for s in matches}
        group_ids = {
            g["GruppenId"] for g in street_groups if g["StrassenId"] in street_ids
        }

        waste_type_names = {w["MuellId"]: w["Art"] for w in waste_types}

        entries = []
        for termin in dates:
            if termin["GruppenId"] not in group_ids:
                continue
            waste_name = waste_type_names.get(termin["Muellart"])
            if not waste_name:
                continue
            date = datetime.strptime(termin["Datum"], "%Y-%m-%d").date()
            entries.append(Collection(date, waste_name, icon=ICON_MAP.get(waste_name)))

        return entries
