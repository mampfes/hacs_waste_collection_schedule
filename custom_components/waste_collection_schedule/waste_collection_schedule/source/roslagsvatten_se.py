import json
import logging
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Roslagsvatten"
DESCRIPTION = "Source for Roslagsvatten waste collection (Österåker, Vaxholm and Ekerö)."
URL = "https://roslagsvatten.se"

VALID_MUNICIPALITIES = {
    "osteraker": "Österåker",
    "vaxholm": "Vaxholm",
    "ekero": "Ekerö",
}

TEST_CASES = {
    "Osteraker Test": {
        "street_address": "Andromedavägen 1, Åkersberga",
        "municipality": "osteraker",
    },
    "Vaxholm Test": {
        "street_address": "Hamngatan 1, Vaxholm",
        "municipality": "vaxholm",
    },
    "Ekerö Test": {
        "street_address": "Ekerö Kyrkväg 1, Ekerö",
        "municipality": "ekero",
    },
}

EXTRA_INFO = [
    {"title": v, "default_params": {"municipality": k}} 
    for k, v in VALID_MUNICIPALITIES.items()
]

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:food-apple",
    "Rest- matavfall": "mdi:trash-can",
    "Slam": "mdi:emoticon-poop",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Street Address (e.g., Andromedavägen 1, Åkersberga)",
        "municipality": "Municipality, one of: 'osteraker', 'vaxholm', or 'ekero'",
    },
    "de": {
        "street_address": "Straßenadresse (z.B. Andromedavägen 1, Åkersberga)",
        "municipality": "Gemeinde, eine von: 'osteraker', 'vaxholm' oder 'ekero'",
    },
    "it": {
        "street_address": "Indirizzo (es. Andromedavägen 1, Åkersberga)",
        "municipality": "Comune, uno di: 'osteraker', 'vaxholm' o 'ekero'",
    },
    "fr": {
        "street_address": "Adresse (par ex. Andromedavägen 1, Åkersberga)",
        "municipality": "Municipalité, l'une des suivantes : 'osteraker', 'vaxholm' ou 'ekero'",
    },
}

class Source:
    def __init__(self, street_address: str, municipality: str):
        self._street_address = street_address
        self._municipality = municipality.lower()
        self._api_url = "https://roslagsvatten.se/schedule"

        if self._municipality not in VALID_MUNICIPALITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, VALID_MUNICIPALITIES.keys()
            )

    def fetch(self):
        # 1. SEARCH for the building ID
        search_payload = {
            "searchText": self._street_address,
            "municipality": self._municipality
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0",
        }

        r = requests.post(
            f"{self._api_url}/search", 
            data=json.dumps(search_payload), 
            headers=headers
        )
        r.raise_for_status()
        
        search_results = r.json()
        if not search_results or "data" not in search_results[0]:
            raise Exception(f"Unexpected API response format during search for: {self._street_address}")

        # Extract data-bid="12345" from the HTML response
        html_search = search_results[0]["data"]
        bid_match = re.search(r'data-bid="(\d+)"', html_search)
        
        if not bid_match:
            raise SourceArgumentException(
                "street_address",
                f"Address '{self._street_address}' not found in municipality '{self._municipality}'. "
                "Please check the spelling or format, test the address on the Roslagsvatten website and try again."
            )
        
        building_id = bid_match.group(1)

        # 2. FETCH the schedule using the building ID
        fetch_payload = {
            "buildingId": building_id,
            "municipality": self._municipality
        }

        r = requests.post(
            f"{self._api_url}/fetch", 
            data=json.dumps(fetch_payload), 
            headers=headers
        )
        r.raise_for_status()
        
        fetch_results = r.json()
        if not fetch_results or "data" not in fetch_results[0]:
            return []

        html_schedule = fetch_results[0]["data"]
        entries = []
        
        # Regex to find all schedule blocks
        pattern = re.compile(r"<h3>(.*?)</h3>[\s\S]*?Nästa hämtning: (.*?)</p>")
        matches = pattern.findall(html_schedule)
        
        for waste_type, date_raw in matches:
            date_raw = date_raw.strip()
            pickup_date = None

            # Pattern 1: Standard YYYY-MM-DD
            if re.match(r"\d{4}-\d{2}-\d{2}", date_raw):
                pickup_date = datetime.strptime(date_raw, "%Y-%m-%d").date()

            # Pattern 2: Week format like "v41 Okt 2026"
            elif "v" in date_raw:
                try:
                    week_match = re.search(r"v(\d+).*?(\d{4})", date_raw)
                    if week_match:
                        week = int(week_match.group(1))
                        year = int(week_match.group(2))
                        # Use ISO week format
                        pickup_date = datetime.strptime(f"{year}-W{week}-1", "%G-W%V-%u").date()
                except Exception as e:
                    _LOGGER.warning(f"Failed to parse week-based date {date_raw}: {e}")

            if pickup_date:
                icon = ICON_MAP.get(waste_type, "mdi:trash-can")
                entries.append(
                    Collection(
                        date=pickup_date,
                        t=waste_type,
                        icon=icon,
                    )
                )

        if not entries:
             _LOGGER.info(f"No collection entries found for address: {self._street_address}")

        return entries