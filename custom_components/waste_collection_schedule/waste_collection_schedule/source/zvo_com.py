from datetime import date, datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "ZVO Entsorgung - Zweckverband Ostholstein"
DESCRIPTION = "Source for ZVO waste collection schedule in Ostholstein, Germany."
URL = "https://www.zvo.com"
COUNTRY = "de"

API_URL = "https://www.zvo.com/api/wastecollection"

TEST_CASES = {
    "Bad Schwartau, Lindenstraße": {
        "city": "Bad Schwartau",
        "street": "Lindenstraße",
    },
    "Curau (no street)": {
        "city": "Curau",
    },
}

EXTRA_INFO = [
    {
        "title": "ZVO Abfuhrkalender",
        "url": "https://www.zvo.com/abfuhrkalender2026",
        "country": "de",
    },
]

ICON_MAP = {
    "Gelbe Tonne": "mdi:recycle",
    "Biotonne": "mdi:leaf",
    "Restmülltonne": "mdi:trash-can",
    "Papiertonne": "mdi:package-variant",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your city and street at https://www.zvo.com/abfuhrkalender2026. "
    "Some smaller towns do not require a street.",
    "de": "Finden Sie Ihren Ort und Ihre Straße unter https://www.zvo.com/abfuhrkalender2026. "
    "Einige kleinere Orte benötigen keine Straße.",
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
        "city": "City name (e.g. 'Bad Schwartau')",
        "street": "Street name (optional for some cities)",
    },
    "de": {
        "city": "Ortsname (z.B. 'Bad Schwartau')",
        "street": "Straßenname (bei einigen Orten nicht erforderlich)",
    },
}


class Source:
    def __init__(self, city: str, street: str = ""):
        if not city:
            raise SourceArgumentRequired("city", "A city name is required")
        self._city = city.strip()
        self._street = street.strip() if street else ""

    @staticmethod
    def _get_cities() -> list[dict]:
        r = requests.get(f"{API_URL}/cities", timeout=30)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _get_streets(city_id: int) -> list[dict]:
        r = requests.post(f"{API_URL}/streets", json={"city": city_id}, timeout=30)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _get_collections(city_id: int, street_id: int) -> list[dict]:
        r = requests.post(
            f"{API_URL}/wastecollection",
            json={"street": street_id, "city": city_id},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _get_dates(collection_id: int) -> list[dict]:
        r = requests.post(
            f"{API_URL}/wastecollectiondates",
            json={"collection": collection_id},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def fetch(self) -> list[Collection]:
        # Step 1: Resolve city
        cities = self._get_cities()
        city_match = None
        for c in cities:
            if c["name"].lower() == self._city.lower():
                city_match = c
                break
        if city_match is None:
            suggestions = [
                c["name"] for c in cities if self._city.lower() in c["name"].lower()
            ]
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "city", self._city, suggestions
                )
            raise SourceArgumentNotFound("city", self._city)

        city_id = city_match["id"]

        # Step 2: Resolve street (optional)
        street_id = 0
        if self._street:
            streets = self._get_streets(city_id)
            street_match = None
            for s in streets:
                if s["name"].lower() == self._street.lower():
                    street_match = s
                    break
            if street_match is None:
                suggestions = [s["name"] for s in streets]
                if suggestions:
                    raise SourceArgumentNotFoundWithSuggestions(
                        "street", self._street, suggestions
                    )
                raise SourceArgumentNotFound("street", self._street)
            street_id = street_match["id"]

        # Step 3: Get collection schedule
        collections = self._get_collections(city_id, street_id)
        if not collections:
            raise SourceArgumentNotFound("city", self._city)

        latest = max(collections, key=lambda x: x["tstamp"])
        collection_color = latest["color"]

        # Step 4: Get dates (API returns full history, filter to recent/future)
        dates = self._get_dates(latest["id"])
        cutoff = date.today().replace(month=1, day=1)

        entries = []
        for item in dates:
            date_str = item["collect_date"]["date"]
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f").date()

            if dt < cutoff:
                continue

            # Every collection date: Gelbe Tonne + Biotonne + Restmülltonne
            entries.append(
                Collection(date=dt, t="Gelbe Tonne", icon=ICON_MAP["Gelbe Tonne"])
            )
            entries.append(Collection(date=dt, t="Biotonne", icon=ICON_MAP["Biotonne"]))
            entries.append(
                Collection(date=dt, t="Restmülltonne", icon=ICON_MAP["Restmülltonne"])
            )

            # Dates matching collection color also get Papiertonne
            if item["color"] == collection_color:
                entries.append(
                    Collection(date=dt, t="Papiertonne", icon=ICON_MAP["Papiertonne"])
                )

        return entries
