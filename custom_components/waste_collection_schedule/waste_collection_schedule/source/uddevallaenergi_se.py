from datetime import date

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Uddevalla Energi"
DESCRIPTION = "Source for Uddevalla Energi waste collection schedules."
URL = "https://www.uddevallaenergi.se/privat/sophamtning.html"
COUNTRY = "se"

TEST_CASES = {
    "Fjällvägen 11, Ljungskile": {
        "address": "Fjällvägen 11, Ljungskile",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Search for your address on the Uddevalla Energi waste collection "
        "webpage and enter it exactly as shown, including the town."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Property address, including the town.",
    },
}

ADDRESS_URL = "https://app.uddevallaenergi.se/wp-json/app/v2/address-flat"
PICKUP_URL = "https://app.uddevallaenergi.se/wp-json/app/v1/next-pickup-web"

HEADERS = {
    "Accept": "application/json",
    "X-App-Identifier": "www.uddevallaenergi.se",
}


def _icon_for_type(collection_type: str) -> Icons | None:
    normalized_type = collection_type.casefold()

    if "matavfall" in normalized_type:
        return Icons.BIO_KITCHEN
    if "restavfall" in normalized_type:
        return Icons.GENERAL_WASTE
    if "trädgårdsavfall" in normalized_type:
        return Icons.GARDEN
    if "kärl 1" in normalized_type or "kärl 2" in normalized_type:
        return Icons.RECYCLING

    return None


class Source:
    def __init__(self, address: str):
        self._address = address

    def _get_plant_number(self) -> str:
        response = requests.get(
            ADDRESS_URL,
            params={"address": self._address.split(",")[0]},
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        hits = [
            hit
            for hit in response.json()
            if not hit.get("is_key") and hit.get("address") and hit.get("plant_number")
        ]

        normalized_address = self._address.strip().casefold()
        for hit in hits:
            if hit["address"].strip().casefold() == normalized_address:
                return hit["plant_number"]

        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            self._address,
            [hit["address"] for hit in hits],
        )

    def fetch(self) -> list[Collection]:
        response = requests.get(
            PICKUP_URL,
            params={"plant_number": self._get_plant_number()},
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        entries = [
            Collection(
                date=date.fromisoformat(item["pickup_date"]),
                t=item["type"],
                icon=_icon_for_type(item["type"]),
            )
            for item in response.json()
        ]

        if not entries:
            raise ValueError("No upcoming collections found for the selected address.")

        return entries
