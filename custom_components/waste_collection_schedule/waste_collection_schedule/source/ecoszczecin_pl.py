from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "EcoSzczecin"
DESCRIPTION = "Source for waste collection schedules in Szczecin, Poland, provided by ecoszczecin.pl."
URL = "https://ecoszczecin.pl"
COUNTRY = "pl"
TEST_CASES = {
    "Tczewska 7A": {"street": "TCZEWSKA", "house_number": "7A"},
    "Aleja Piastów 1": {"street": "ALEJA PIASTÓW", "house_number": "1"},
    "Bolesława Krzywoustego 1": {
        "street": "Bolesława Krzywoustego",
        "house_number": "1",
    },
}

API_URL = "https://api.ecoszczecin.pl/api/v1"
LOCATION = "SZCZECIN"

ICON_MAP = {
    "Odpady zmieszane": Icons.GENERAL_WASTE,
    "Bioodpady": Icons.ORGANIC,
    "Metale i tworzywa sztuczne": Icons.PLASTIC_PACKAGING,
    "Papier": Icons.PAPER,
    "Szkło": Icons.GLASS,
    "Odpady wielkogabarytowe": Icons.BULKY,
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
        "house_number": "House Number",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": (
            "Street name in Szczecin, as shown on ecoszczecin.pl "
            "(e.g. 'TCZEWSKA'). Not case-sensitive."
        ),
        "house_number": (
            "House number for the given street, as shown on ecoszczecin.pl (e.g. '7A')."
        ),
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://ecoszczecin.pl/harmonogramy/, choose your street and "
        "house number from the dropdowns, and copy their values exactly as "
        "shown."
    ),
}


class Source:
    def __init__(self, street: str, house_number: str):
        self._street = street.strip()
        self._house_number = house_number.strip()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0"})

    def _get_streets(self) -> list[str]:
        response = self._session.get(f"{API_URL}/search/locations", timeout=30)
        response.raise_for_status()
        return response.json().get("data", [])

    def _resolve_street(self) -> str:
        streets = self._get_streets()
        target = self._street.strip().casefold()
        for street in streets:
            if street.casefold() == target:
                return street
        raise SourceArgumentNotFoundWithSuggestions(
            "street", self._street, suggestions=streets
        )

    def _get_house_numbers(self, street: str) -> list[str]:
        response = self._session.get(
            f"{API_URL}/search/number",
            params={"filter[location]": LOCATION, "filter[street]": street},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("data", [])

    def _resolve_house_number(self, street: str) -> str:
        numbers = self._get_house_numbers(street)
        target = self._house_number.strip().casefold()
        for number in numbers:
            if number.casefold() == target:
                return number
        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", self._house_number, suggestions=numbers
        )

    def fetch(self) -> list[Collection]:
        street = self._resolve_street()
        house_number = self._resolve_house_number(street)

        response = self._session.get(
            f"{API_URL}/search/calendar",
            params={
                "filter[location]": LOCATION,
                "filter[street]": street,
                "filter[number]": house_number,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        calendar = data.get("calendar")
        entries: list[Collection] = []
        if not isinstance(calendar, dict):
            return entries

        for months in calendar.values():
            for days in months.values():
                for day in days:
                    collection_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
                    for waste_type in day.get("types", []):
                        entries.append(
                            Collection(
                                date=collection_date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )

        return entries
