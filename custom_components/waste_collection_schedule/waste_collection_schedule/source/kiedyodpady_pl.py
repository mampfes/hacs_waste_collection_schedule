from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Kiedy Odpady (kiedyodpady.pl)"
DESCRIPTION = (
    "Source for Polish municipalities using the kiedyodpady.pl "
    "(mOdpady / mMieszkaniec) waste collection platform."
)
URL = "https://kiedyodpady.pl"
COUNTRY = "pl"

EXTRA_INFO = [
    {
        "title": "Wieliczka",
        "url": "https://wieliczka.kiedyodpady.pl",
        "country": "pl",
        "default_params": {"municipality": "wieliczka"},
    },
    {
        "title": "Pabianice",
        "url": "https://pabianice.kiedyodpady.pl",
        "country": "pl",
        "default_params": {"municipality": "pabianice"},
    },
]

TEST_CASES = {
    "Wieliczka (miasto), ul. Adama Asnyka, pozostałe": {
        "municipality": "wieliczka",
        "city": "Wieliczka (miasto)",
        "street": "ul. Adama Asnyka",
        "number": "pozostałe",
    },
    'Pabianice (miasto), ul. 15 Pułku Piechoty "Wilków", pozostałe': {
        "municipality": "pabianice",
        "city": "Pabianice (miasto)",
        "street": 'ul. 15 Pułku Piechoty "Wilków"',
        "number": "pozostałe",
    },
}

API_URL = "https://api.kiedyodpady.pl/public"
DEFAULT_LOOKAHEAD_DAYS = 365

ICON_MAP = {
    "bio": Icons.ORGANIC,
    "paper": Icons.PAPER,
    "plastics": Icons.PLASTIC_PACKAGING,
    "glass": Icons.GLASS,
    "mixed": Icons.GENERAL_WASTE,
    "bulky": Icons.BULKY,
    "constructionWaste": Icons.BULKY,
    "hazardous": Icons.HAZARDOUS,
    "ewaste": Icons.ELECTRONICS,
    "battery": Icons.BATTERY,
    "textile": Icons.TEXTILE,
    "tree": Icons.CHRISTMAS_TREE,
    "garden": Icons.GARDEN,
    "metal": Icons.METAL,
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "city": "City Name",
        "street": "Street Name",
        "number": "House Number",
        "lookahead_days": "Lookahead Days",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": (
            "Subdomain slug for your municipality on kiedyodpady.pl, "
            "e.g. 'pabianice' for pabianice.kiedyodpady.pl."
        ),
        "city": "City/locality name as shown in the kiedyodpady.pl UI.",
        "street": "Street name as shown in the kiedyodpady.pl UI (optional for some localities).",
        "number": "House number / address entry as shown in the kiedyodpady.pl UI (optional).",
        "lookahead_days": (
            "Number of days ahead to fetch the schedule. "
            "Defaults to 365, matching the official Android app."
        ),
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://{municipality}.kiedyodpady.pl (e.g. https://pabianice.kiedyodpady.pl) "
        "and step through the address selection. "
        "The municipality value is the subdomain prefix (everything before '.kiedyodpady.pl'). "
        "Copy the city, street, and house-number values exactly as displayed in the dropdown lists."
    ),
}

SOURCE_CODEOWNERS = ["@dominik-korsa"]


def _normalize(value: str) -> str:
    return value.strip().lower().casefold()


def _pick_icon(icon_slug: str | None) -> str | None:
    if not icon_slug:
        return None
    return ICON_MAP.get(icon_slug)


class Source:
    def __init__(
        self,
        municipality: str,
        city: str,
        street: str | None = None,
        number: str | None = None,
        lookahead_days: int = DEFAULT_LOOKAHEAD_DAYS,
    ):
        self._municipality = municipality.strip().lower()
        self._city = city.strip()
        self._street = street.strip() if isinstance(street, str) else None
        self._number = number.strip() if isinstance(number, str) else None
        self._lookahead_days = int(lookahead_days)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Origin": f"https://{self._municipality}.kiedyodpady.pl",
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

    def _get_waste_type_map(self) -> dict[str, tuple[str, str | None]]:
        response = self._session.get(f"{API_URL}/waste-types", timeout=30)
        response.raise_for_status()
        result: dict[str, tuple[str, str | None]] = {}
        for item in response.json():
            if "id" in item:
                result[item["id"]] = (item.get("name", item["id"]), item.get("icon"))
        return result

    def fetch(self) -> list[Collection]:
        locality_id = self._resolve_city_id()
        street_id = self._resolve_street_id(locality_id)
        self._validate_number(locality_id, street_id)
        waste_type_map = self._get_waste_type_map()

        today = date.today()
        date_to = today + timedelta(days=self._lookahead_days)
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
            waste_id = occurrence.get("what", "")
            waste_name, icon_slug = waste_type_map.get(waste_id, (waste_id, None))
            entries.append(
                Collection(
                    date=datetime.fromisoformat(occurrence["when"]).date(),
                    t=waste_name,
                    icon=_pick_icon(icon_slug),
                )
            )

        return entries
