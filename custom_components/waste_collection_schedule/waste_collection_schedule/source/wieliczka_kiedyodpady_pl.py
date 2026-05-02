from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Wieliczka Kiedy Odpady"
DESCRIPTION = "Source for Wieliczka Kiedy Odpady schedules."
URL = "https://wieliczka.kiedyodpady.pl"
COUNTRY = "pl"

TEST_CASES = {
    "Wieliczka (miasto), ul. Adama Asnyka, pozostałe": {
        "city": "Wieliczka (miasto)",
        "street": "ul. Adama Asnyka",
        "number": "pozostałe",
    }
}

API_URL = "https://api.kiedyodpady.pl/public"
ORIGIN = "https://wieliczka.kiedyodpady.pl"
DEFAULT_DAYS = 35

ICON_MAP = {
    "bio": "mdi:leaf",
    "papier": "mdi:package-variant",
    "metale": "mdi:recycle",
    "tworzywa": "mdi:recycle",
    "szkło": "mdi:bottle-soda",
    "zmieszane": "mdi:trash-can",
    "gabaryt": "mdi:sofa",
    "choinka": "mdi:pine-tree",
    "odpady zielone": "mdi:leaf",
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City Name",
        "street": "Street Name",
        "number": "House Number",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Open https://wieliczka.kiedyodpady.pl and select your location. Use the city name, street name, and house number exactly as shown in the UI.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "City name from the Kiedy Odpady locality list.",
        "street": "Street name from the selected city.",
        "number": "House number/address value from the selected street.",
    }
}


def _normalize(value: str) -> str:
    return value.strip().lower().casefold()


def _pick_icon(name: str) -> str | None:
    lowered = name.lower()
    for key, icon in ICON_MAP.items():
        if key in lowered:
            return icon
    return None


class Source:
    def __init__(
        self,
        city: str,
        street: str | None = None,
        number: str | None = None,
    ):
        self._city = city
        self._street = street.strip() if isinstance(street, str) else None
        self._number = number.strip() if isinstance(number, str) else None
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Origin": ORIGIN,
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            }
        )

    def _get_localities(self) -> list[dict]:
        response = self._session.get(f"{API_URL}/territory/localities", timeout=30)
        response.raise_for_status()
        return response.json()

    def _resolve_city_id(self) -> str:
        localities = self._get_localities()
        target = _normalize(self._city)

        for locality in localities:
            extended_name = locality.get("extendedName", "")
            if extended_name and _normalize(extended_name) == target:
                return locality["id"]

        suggestions = [
            locality.get("extendedName")
            for locality in localities
            if locality.get("extendedName")
        ]
        raise SourceArgumentNotFoundWithSuggestions(
            "city",
            self._city,
            suggestions=suggestions,
        )

    def _get_streets(self, locality_id: str) -> list[dict]:
        response = self._session.get(
            f"{API_URL}/territory/localities/{locality_id}/streets",
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def _resolve_street_id(self, locality_id: str) -> str | None:
        if not self._street:
            return None
        streets = self._get_streets(locality_id)
        target = _normalize(self._street)

        for street in streets:
            extended_name = street.get("extendedName", "")
            if extended_name and _normalize(extended_name) == target:
                return street["id"]

        suggestions = [
            street.get("extendedName")
            for street in streets
            if street.get("extendedName")
        ]
        raise SourceArgumentNotFoundWithSuggestions(
            "street",
            self._street,
            suggestions=suggestions,
        )

    def _validate_number(self, locality_id: str, street_id: str | None) -> None:
        if not street_id or not self._number:
            return
        response = self._session.get(
            f"{API_URL}/territory/localities/{locality_id}/addresses/{street_id}",
            timeout=30,
        )
        response.raise_for_status()
        numbers = response.json()
        if self._number not in numbers:
            raise SourceArgumentNotFoundWithSuggestions(
                "number",
                self._number,
                suggestions=numbers,
            )

    def _get_waste_types(self) -> dict[str, str]:
        response = self._session.get(f"{API_URL}/waste-types", timeout=30)
        response.raise_for_status()
        return {item["id"]: item["name"] for item in response.json() if "id" in item}

    def fetch(self) -> list[Collection]:
        locality_id = self._resolve_city_id()
        street_id = self._resolve_street_id(locality_id)
        self._validate_number(locality_id, street_id)
        waste_type_map = self._get_waste_types()

        today = date.today()
        date_to = today + timedelta(days=DEFAULT_DAYS)
        payload = {
            "from": today.isoformat(),
            "to": date_to.isoformat(),
            "queries": [
                {
                    "localityId": locality_id,
                    "streetId": street_id or "",
                    "number": self._number or "",
                    "propertyType": "",
                    "buildingType": "",
                }
            ],
        }

        response = self._session.post(
            f"{API_URL}/schedules/find",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        entries: list[Collection] = []
        for occurrence in data.get("occurrences", []):
            waste_name = waste_type_map.get(occurrence["what"], occurrence["what"])
            entries.append(
                Collection(
                    date=datetime.fromisoformat(occurrence["when"]).date(),
                    t=waste_name,
                    icon=_pick_icon(waste_name),
                )
            )

        return entries
