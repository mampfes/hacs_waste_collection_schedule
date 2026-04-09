from datetime import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "SmiecioPlan"
DESCRIPTION = "Source for SmiecioPlan.pl waste collection schedules."
URL = "https://smiecioplan.pl"
COUNTRY = "pl"

TEST_CASES = {
    "Szczecin, Aleja Wojska Polskiego 2": {
        "city": "szczecin",
        "street": "ALEJA WOJSKA POLSKIEGO",
        "house": "2",
    },
    "Gdansk, Abrahama 1": {
        "city": "gdansk",
        "street": "ABRAHAMA",
        "house": "1",
    },
}

ICON_MAP = {
    "zmieszane": "mdi:trash-can",
    "bio": "mdi:leaf",
    "papier": "mdi:package-variant",
    "szk": "mdi:bottle-wine",
    "metal": "mdi:recycle",
    "wielkogabaryt": "mdi:sofa",
}

EXTRA_INFO = [
    {
        "title": "Szczecin",
        "url": "https://smiecioplan.pl",
        "default_params": {"city": "szczecin"},
    },
    {
        "title": "Gdańsk",
        "url": "https://smiecioplan.pl",
        "default_params": {"city": "gdansk"},
    },
    {
        "title": "Gdynia",
        "url": "https://smiecioplan.pl",
        "default_params": {"city": "gdynia"},
    },
    {
        "title": "Sopot",
        "url": "https://smiecioplan.pl",
        "default_params": {"city": "sopot"},
    },
]

API_URL = "https://smiecioplan.pl/wp-json/smiecioplan/v1"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to https://smiecioplan.pl and search for your address. Use the city, street name (uppercase), and house number.",
    "de": "Gehen Sie auf https://smiecioplan.pl und suchen Sie nach Ihrer Adresse. Verwenden Sie die Stadt, den Straßennamen (Großbuchstaben) und die Hausnummer.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "City name (szczecin, gdansk, gdynia, or sopot).",
        "street": "Street name in uppercase as shown on SmiecioPlan.",
        "house": "House number.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
        "house": "House Number",
    },
    "de": {
        "city": "Stadt",
        "street": "Straße",
        "house": "Hausnummer",
    },
}


def _get_icon(summary: str) -> str | None:
    lower = summary.lower()
    for key, icon in ICON_MAP.items():
        if key in lower:
            return icon
    return None


class Source:
    def __init__(self, city: str, street: str, house: str | int):
        if not city:
            raise SourceArgumentRequired("city", "City is required.")
        if not street:
            raise SourceArgumentRequired("street", "Street is required.")
        if not house:
            raise SourceArgumentRequired("house", "House number is required.")

        self._city = city.strip().lower()
        self._street = street.strip().upper()
        self._house = str(house).strip()

    def fetch(self) -> list[Collection]:
        # Validate street exists
        search_params: dict[str, str | int] = {
            "q": self._street,
            "city": self._city,
            "limit": 50,
        }
        r = requests.get(
            f"{API_URL}/search",
            params=search_params,
            timeout=30,
        )
        r.raise_for_status()
        streets = r.json()

        matching = [s for s in streets if s["street"].upper() == self._street]
        if not matching:
            suggestions = [s["street"] for s in streets]
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, suggestions=suggestions
            )

        # Validate house number exists
        houses_params: dict[str, str | int] = {
            "street": self._street,
            "city": self._city,
            "limit": 500,
        }
        r = requests.get(
            f"{API_URL}/houses",
            params=houses_params,
            timeout=30,
        )
        r.raise_for_status()
        houses = r.json()

        if self._house not in houses:
            raise SourceArgumentNotFoundWithSuggestions(
                "house", self._house, suggestions=houses[:20]
            )

        # Fetch ICS
        r = requests.get(
            f"{API_URL}/export/ics",
            params={
                "street": self._street,
                "house": self._house,
                "city": self._city,
                "types": "mixed,segregated,bio,bulky",
            },
            timeout=30,
        )
        r.raise_for_status()

        entries: list[Collection] = []
        current_summary = None
        current_date = None

        for line in r.text.split("\n"):
            line = line.strip()
            if line.startswith("SUMMARY:"):
                current_summary = line[8:]
            elif line.startswith("DTSTART;VALUE=DATE:"):
                current_date = datetime.strptime(line[19:], "%Y%m%d").date()
            elif line == "END:VEVENT" and current_summary and current_date:
                entries.append(
                    Collection(
                        date=current_date,
                        t=current_summary,
                        icon=_get_icon(current_summary),
                    )
                )
                current_summary = None
                current_date = None

        return entries
