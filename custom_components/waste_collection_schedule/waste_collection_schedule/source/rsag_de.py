import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "RSAG Rhein-Sieg Abfallwirtschaftsgesellschaft"
DESCRIPTION = "Source for RSAG waste collection in the Rhein-Sieg-Kreis, Germany."
URL = "https://www.rsag.de"
COUNTRY = "de"

TEST_CASES = {
    "Königswinter, Winzerstraße": {
        "city": "Königswinter",
        "street": "Winzerstraße",
    },
    "Siegburg, Annostraße": {
        "city": "Siegburg",
        "street": "Annostraße",
    },
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Bio": Icons.ORGANIC,
    "Papier": Icons.PAPER,
    "Wertstoff": Icons.PLASTIC_PACKAGING,
    "Weihnachtsbaum": Icons.CHRISTMAS_TREE,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit [https://www.rsag.de/abfallkalender/abfuhrtermine](https://www.rsag.de/abfallkalender/abfuhrtermine) and select your city and street. Use the exact city and street names shown in the form.",
    "de": "Besuchen Sie [https://www.rsag.de/abfallkalender/abfuhrtermine](https://www.rsag.de/abfallkalender/abfuhrtermine) und wählen Sie Ihren Ort und Ihre Straße. Verwenden Sie die genauen Namen wie in der Auswahlliste.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
    },
    "de": {
        "city": "Ort",
        "street": "Straße",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Name of the city/municipality, e.g. 'Königswinter'",
        "street": "Name of the street, e.g. 'Winzerstraße'",
    },
    "de": {
        "city": "Name des Ortes, z.B. 'Königswinter'",
        "street": "Name der Straße, z.B. 'Winzerstraße'",
    },
}

API_BASE = "https://www.rsag.de/api"


def _normalise(s: str) -> str:
    """Lowercase and strip for fuzzy matching."""
    return s.strip().lower()


class Source:
    def __init__(self, city: str, street: str):
        self._city = city
        self._street = street
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # 1. Resolve city → city_id
        r = session.get(f"{API_BASE}/city/all")
        r.raise_for_status()
        cities = r.json()

        city_id = None
        city_names = []
        for c in cities:
            city_names.append(c["name"])
            if _normalise(c["name"]) == _normalise(self._city):
                city_id = c["city_id"]
                break

        if city_id is None:
            raise SourceArgumentNotFoundWithSuggestions("city", self._city, city_names)

        # 2. Resolve street → street_id
        r = session.get(f"{API_BASE}/street/filter/{city_id}")
        r.raise_for_status()
        streets = r.json()

        street_id = None
        street_names = []
        for s in streets:
            street_names.append(s["name"])
            if _normalise(s["name"]) == _normalise(self._street):
                street_id = s["street_id"]
                break

        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, street_names
            )

        # 3. Fetch all waste type IDs (use all by default)
        r = session.get(f"{API_BASE}/wastetype/all")
        r.raise_for_status()
        waste_type_ids = ",".join(str(w["wastetype_id"]) for w in r.json())

        # 4. Fetch active months — request a rolling 12-month window
        today = datetime.date.today()
        months = []
        for i in range(12):
            month = today.replace(day=1) + datetime.timedelta(days=32 * i)
            month = month.replace(day=1)
            months.append(month.strftime("%Y-%m"))
        months_param = ",".join(months)

        # 5. Fetch ICS calendar
        ics_url = (
            f"{API_BASE}/pickup/filter/{street_id}/{waste_type_ids}/{months_param}/ics"
        )
        r = session.get(ics_url)
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            waste_type = d[1]
            icon = None
            for key, value in ICON_MAP.items():
                if key.lower() in waste_type.lower():
                    icon = value
                    break
            entries.append(Collection(d[0], waste_type, icon=icon))

        return entries
