from datetime import date

import requests

from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Stockholm Vatten och Avfall"
DESCRIPTION = "Source for Stockholm Vatten och Avfall waste collection schedules."
URL = (
    "https://www.stockholmvattenochavfall.se/"
    "villa-och-radhus/avfallstjanster/"
    "nar-kommer-sopbilen/"
)
COUNTRY = "se"

TEST_CASES = {
    "Lussekattsvägen 10": {
        "street_address": "Lussekattsvägen 10, Sköndal, 128 69",
    },
    "Nässelstigen 7": {
        "street_address": "Nässelstigen 7, Hässelby, 165 65",
    },
    "Skogsvägen 6": {
        "street_address": "Skogsvägen 6, Enskede, 122 62",
    },
}

AUTOCOMPLETE_URL = (
    "https://www.stockholmvattenochavfall.se/"
    "villa-och-radhus/avfallstjanster/"
    "nar-kommer-sopbilen/"
    "AutoCompleteMe"
)

SEARCH_URL = (
    "https://www.stockholmvattenochavfall.se/"
    "villa-och-radhus/avfallstjanster/"
    "nar-kommer-sopbilen/"
    "Search"
)

ICON_MAP = {
    "Kärl 1 - restavfall och matavfall": Icons.GENERAL_WASTE,
    "Kärl 2 - papper och plast": Icons.RECYCLING,
    "Kärl 3 - glas och metall": Icons.GLASS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the complete address as shown by the Stockholm "
        "Vatten och Avfall address search."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street Address",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": (
            "Complete address including locality and postal code."
        ),
    }
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address.strip()
        self._session = requests.Session()

    def _validate_address(self):
        query = self._street_address.split(",")[0].strip()

        response = self._session.get(
            AUTOCOMPLETE_URL,
            params={"query": query},
            timeout=30,
        )
        response.raise_for_status()

        suggestions = response.json()

        for suggestion in suggestions:
            if (
                suggestion["value"].casefold()
                == self._street_address.casefold()
            ):
                return

        if suggestions:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_address",
                self._street_address,
                [s["value"] for s in suggestions],
            )

        raise SourceArgumentNotFound(
            "street_address",
            self._street_address,
        )

    def fetch(self):
        self._validate_address()

        response = self._session.get(
            SEARCH_URL,
            params={
                "address": self._street_address,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        entries = []

        for item in data:
            collection_date = date.fromisoformat(
                item["executionDate"]
            )

            waste_type = item["group"]

            entries.append(
                Collection(
                    collection_date,
                    waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return sorted(entries, key=lambda x: x.date)
        
