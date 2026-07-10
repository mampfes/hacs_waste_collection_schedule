from datetime import date

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Hedemora Energi"
DESCRIPTION = "Source for Hedemora Energi waste collection schedules, Sweden."
URL = "https://www.hedemoraenergi.se/"
COUNTRY = "se"
TEST_CASES = {
    "Åsgatan 28": {"address": "Åsgatan 28"},
    "Pickup ID 1392000": {"pickup_id": "1392000"},
}

API_URL = "https://www.hedemoraenergi.se/wp-json/internal/v1/fetchplanner"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HomeAssistant-WCS/1.0)"}

ICON_MAP = {
    "Brännbart": Icons.GENERAL_WASTE,
    "Kompost": Icons.BIO_KITCHEN,
    "Matavfall": Icons.BIO_KITCHEN,
}
DEFAULT_ICON = Icons.GENERAL_WASTE

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Use `pickup_id` if known. Otherwise enter the exact address as shown in Hedemora Energi's fetch planner search.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
        "pickup_id": "Pickup ID",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Address to search for. Required only when pickup_id is not provided.",
        "pickup_id": "Hedemora Energi pickup ID. Preferred when known.",
    },
}


class Source:
    def __init__(self, address: str | None = None, pickup_id: str | None = None):
        if not address and not pickup_id:
            raise SourceArgumentRequired(
                "pickup_id",
                "Either pickup_id or address is required to fetch the collection schedule.",
            )

        self._address = address.strip() if address else None
        self._pickup_id = pickup_id.strip() if pickup_id else None

    def fetch(self) -> list[Collection]:
        pickup_id = self._pickup_id or self._get_pickup_id()

        r = requests.get(
            f"{API_URL}/calendar",
            params={"pickup_id": pickup_id},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()

        data = r.json()
        if data.get("success") is not True:
            raise ValueError("Unexpected response from Hedemora Energi calendar API")

        entries = []
        seen = set()
        for item in data.get("data", []):
            waste_type = item["ContentType"]
            collection_date = date.fromisoformat(item["ExecutionDate"])
            key = (collection_date, waste_type)
            if key in seen:
                continue
            seen.add(key)

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, DEFAULT_ICON),
                )
            )

        return entries

    def _get_pickup_id(self) -> str:
        if not self._address:
            raise SourceArgumentRequired(
                "address",
                "Address is required when pickup_id is not provided.",
            )

        r = requests.post(
            f"{API_URL}/search",
            params={"address": self._address},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()

        data = r.json()
        if data.get("success") is not True:
            raise ValueError("Unexpected response from Hedemora Energi search API")

        results = data.get("results", [])
        if not results:
            raise SourceArgumentNotFound("address", self._address)

        if len(results) > 1:
            suggestions = [
                _format_address_suggestion(result)
                for result in results
                if result.get("address")
            ]
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                self._address,
                suggestions,
            )

        return results[0]["id"]


def _format_address_suggestion(result: dict) -> str:
    address = result["address"]
    city = result.get("city")
    zip_code = result.get("zipCode")

    if city and zip_code:
        return f"{address}, {zip_code} {city}"
    if city:
        return f"{address}, {city}"
    return address
