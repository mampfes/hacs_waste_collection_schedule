import json
import re
import requests
from datetime import datetime
from typing import Dict, List, Any
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentException
)

TITLE = "PreZero Bielsko-Biała"
DESCRIPTION = "Source for PreZero Bielsko-Biała waste collection schedule"
URL = "https://prezero-bielsko.pl/harmonogram-odbioru-odpadow/"

TEST_CASES = {
    "Test_001": {"street": "Krakowska", "house_nuber": "12"},
    "Test_002": {"street": "1 Maja", "house_nuber": "10"},
    "Test_003": {"street": "Bajki", "house_nuber": "12A"},
    "Test_004": {"street": "Chabrowa", "house_nuber": "1B"}
}

API_URL = "https://prezero-bielsko.pl/harmonogramy/index.php"

WASTE_TYPE_MAP = {
    "kuchenne": "Bio",
    "resztkowe": "Pozostałości po segregowaniu",
    "makulatura": "Papier",
    "szklo": "Szkło",
    "mix": "Metale i tworzywa sztuczne",
    "zielone": "Zielone",
    "gabaryty": "Gabaryty"
}

ICON_MAP = {
    "kuchenne": "mdi:bio",
    "resztkowe": "mdi:trash-can",
    "makulatura": "mdi:newspaper",
    "szklo": "mdi:glass-fragile",
    "mix": "mdi:recycle",
    "zielone": "mdi:flower-tulip",
    "gabaryty": "mdi:table-furniture"
}

#### Arguments affecting the configuration GUI ####

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street",
        "house_number": "House number",
    },
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
    },
    "it": {
        "street": "Via",
        "house_number": "Numero civico",
    },
    "fr": {
        "street": "Rue",
        "house_number": "Numéro de maison",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
        "house_number": "House number",
    },
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
    },
    "it": {
        "street": "Via",
        "house_number": "Numero civico",
    },
    "fr": {
        "street": "Rue",
        "house_number": "Numéro de maison",
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self, street: str, house_number: str):
        self._city = "Bielsko-Biała"
        self._street = street
        self._house_number = house_number
        self._year = datetime.now().year

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        match = re.search(r'eval\((.*)\)', response_text)
        if not match:
            raise SourceArgumentException("Server response does not match expected format.")

        json_data = match.group(1).strip()
        json_data = re.sub(r',\s*([\]}])', r'\1', json_data)
        try:
            return json.loads(json_data)
        except json.JSONDecodeError as e:
            raise SourceArgumentException(f"JSON parsing error: {e}\nReceived content: {json_data}")

    def _post_request(self, payload: Dict[str, str]) -> Dict[str, Any]:
        headers = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-requested-with": "XMLHttpRequest",
        }

        try:
            response = requests.post(API_URL, headers=headers, data=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise SourceArgumentException(f"API communication error: {e}")

        return self._extract_json_from_response(response.text)

    def _validate_api_response_data(self, data: Dict[str, Any], data_description: str) -> None:
        if "dane" not in data or not isinstance(data["dane"], list):
            raise SourceArgumentException(f"Error downloading {data_description}. Incorrect API response structure: {data}")

    def _get_streets(self) -> List[str]:
        payload = {
            "option": "com_sita",
            "view": "ulice",
            "q": self._city,
            "rok": str(self._year),
        }
        data = self._post_request(payload)
        print(f"API RESPONSE (Streets): {data}")
        self._validate_api_response_data(data, "streets")

        return [street["ulica"] for street in data["dane"] if "ulica" in street]

    def _get_house_numbers(self) -> List[str]:
        payload = {
            "option": "com_sita",
            "view": "numery",
            "q": self._city,
            "ulica": self._street,
            "rok": str(self._year),
        }
        data = self._post_request(payload)
        print(f"API RESPONSE (House numbers): {data}")
        self._validate_api_response_data(data, f"house numbers for street '{self._street}'")

        return [house["numer"] for house in data["dane"] if "numer" in house]

    def _get_symbol(self) -> str:
        available_streets = self._get_streets()
        street_lower = self._street.lower()

        matched_street = next((street for street in available_streets if street.lower() == street_lower), None)
        if not matched_street:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, available_streets
            )

        self._street = matched_street

        available_numbers = self._get_house_numbers()
        if self._house_number not in available_numbers:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, available_numbers
            )

        payload = {
            "option": "com_sita",
            "view": "typy",
            "q": self._city,
            "ulica": self._street,
            "numer": self._house_number,
            "rok": str(self._year),
        }

        data = self._post_request(payload)
        self._validate_api_response_data(data, "symbol")

        if not data["dane"]:
            raise SourceArgumentException(f"Could not find symbol for the given address. API response data is empty: {data}")


        return data["dane"][0]["symbol"]

    def fetch(self) -> List[Collection]:
        symbol = self._get_symbol()

        payload = {
            "option": "com_sita",
            "view": "daty",
            "q": symbol,
            "rok": str(self._year),
        }

        data = self._post_request(payload)
        self._validate_api_response_data(data, "schedule")

        entries = []
        for item in data["dane"]:
            date_str = f"{self._year}-{item['data_m']}-{item['data_d']}"
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            waste_type = WASTE_TYPE_MAP.get(item["rodzaj"], "unknown")
            icon = ICON_MAP.get(item["rodzaj"])
            entries.append(Collection(date, waste_type))

        return entries