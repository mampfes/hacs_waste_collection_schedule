import unicodedata
import uuid
from datetime import date, datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Montri"
DESCRIPTION = (
    "Source for Montri, a French waste collection schedule platform used by "
    "several intercommunal waste-management syndicates (e.g. SICOVAD around "
    "Épinal)."
)
URL = "https://montri.fr"
COUNTRY = "fr"

TEST_CASES = {
    "6 Place Georges Boizot, Dinozé": {
        "postal_code": "88000",
        "city_name": "Dinozé",
        "address": "6 Place Georges Boizot",
    },
    "2 Place Georges Clémenceau, Épinal": {
        "postal_code": "88000",
        "city_name": "Épinal",
        "address": "2 place georges clémenceau",
    },
}

ICON_MAP = {
    "householdtrash": Icons.GENERAL_WASTE,
    "recyclable": Icons.PLASTIC_PACKAGING,
    "glass": Icons.GLASS,
    "paper": Icons.PAPER,
    "organic": Icons.ORGANIC,
    "bulky": Icons.BULKY,
}
DEFAULT_ICON = Icons.GENERAL_WASTE

PARAM_TRANSLATIONS = {
    "en": {
        "postal_code": "Postal code",
        "city_name": "City name",
        "address": "Address",
    },
    "fr": {
        "postal_code": "Code postal",
        "city_name": "Nom de la commune",
        "address": "Adresse",
    },
}
PARAM_DESCRIPTIONS = {
    "en": {
        "postal_code": "The postal code of your municipality, e.g. 88000.",
        "city_name": (
            "The exact name of your municipality as shown on "
            "https://montri.fr, e.g. 'Dinozé'."
        ),
        "address": (
            "The street address to search for (house number and street "
            "name), e.g. '6 Place Georges Boizot'."
        ),
    },
    "fr": {
        "postal_code": "Le code postal de votre commune, par exemple 88000.",
        "city_name": (
            "Le nom exact de votre commune tel qu'affiché sur "
            "https://montri.fr, par exemple 'Dinozé'."
        ),
        "address": (
            "L'adresse à rechercher (numéro et nom de rue), par exemple "
            "'6 Place Georges Boizot'."
        ),
    },
}

API_BASE = "https://frontend.montri.fr"
TIMEZONE = ZoneInfo("Europe/Paris")
MONTHS_AHEAD = 6


def _normalize(value: str) -> str:
    """Lowercase and strip accents for fuzzy comparisons."""
    normalized = unicodedata.normalize("NFKD", value)
    return (
        "".join(c for c in normalized if not unicodedata.combining(c)).lower().strip()
    )


def _parse_local_date(iso_datetime: str) -> date:
    dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    return dt.astimezone(TIMEZONE).date()


class Source:
    def __init__(self, postal_code: str, city_name: str, address: str):
        self._postal_code = postal_code.strip()
        self._city_name = city_name.strip()
        self._address = address.strip()

    def _sign_in_anonymously(
        self,
        session: requests.Session,
        contract_id: str,
        city_insee_code: str,
        address_id: str,
    ) -> str:
        body = {
            "addressId": address_id,
            "cityInseeCode": city_insee_code,
            "contractId": contract_id,
            "isCguAccepted": False,
            "notificationGenerals": False,
            "notificationNews": False,
            "notificationPerturbations": False,
            "notificationRecyclingCenter": False,
            "notificationToken": "",
            "selectedRecyclingCenterId": "",
            "sorterLevel": "debutant",
            "userId": str(uuid.uuid4()),
            "userType": "PRIVATE",
        }
        r = session.post(f"{API_BASE}/v1/auth/signInAnonymously", json=body, timeout=60)
        r.raise_for_status()
        return str(r.json()["currentAccessToken"])

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # 1. Resolve postal code + city name -> cityInseeCode / contractId
        r = session.get(f"{API_BASE}/v1/city/find/{self._postal_code}", timeout=100)
        r.raise_for_status()
        cities = r.json()

        city = None
        city_names = []
        for c in cities:
            city_names.append(c["cityName"])
            if _normalize(c["cityName"]) == _normalize(self._city_name):
                city = c
                break

        if city is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city_name", self._city_name, sorted(set(city_names))
            )

        # 2. Anonymous sign-in bound to the contract, to authorize address search
        token = self._sign_in_anonymously(
            session, city["contractId"], city["inseeCode"], ""
        )
        session.headers["Authorization"] = f"Bearer {token}"

        # 3. Search for the address within the contract
        address = quote(self._address, safe="")
        r = session.get(
            f"{API_BASE}/v1/address/search/bycontract/{address}", timeout=100
        )
        r.raise_for_status()
        candidates = r.json()

        match = None
        for candidate in candidates:
            if candidate.get("citycode") == city["inseeCode"]:
                match = candidate
                break

        if match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [c["label"] for c in candidates],
            )

        # 4. Re-authenticate, this time bound to the resolved address
        token = self._sign_in_anonymously(
            session, city["contractId"], city["inseeCode"], match["id"]
        )
        session.headers["Authorization"] = f"Bearer {token}"

        # 5. Fetch human-readable names for the door-to-door ("pap") waste flows
        r = session.get(f"{API_BASE}/v1/contract/trashflows", timeout=100)
        r.raise_for_status()
        flow_names = {
            flow["code"]: flow["name"] for flow in r.json() if flow.get("type") == "pap"
        }

        # 6. Fetch a rolling window of monthly calendars
        entries = []
        today = date.today()
        month = today.month
        year = today.year
        for _ in range(MONTHS_AHEAD):
            r = session.get(
                f"{API_BASE}/v1/calendar/tablemonth/fixed/{month}/{year}", timeout=100
            )
            r.raise_for_status()
            table = r.json()

            for week in table.get("weeks", []):
                for day in week.values():
                    iso_date = day.get("date")
                    if not iso_date:
                        continue
                    collection_date = _parse_local_date(iso_date)
                    for code in day.get("data", []):
                        name = flow_names.get(code, code)
                        entries.append(
                            Collection(
                                date=collection_date,
                                t=name,
                                icon=ICON_MAP.get(code, DEFAULT_ICON),
                            )
                        )

            month += 1
            if month > 12:
                month = 1
                year += 1

        return entries
