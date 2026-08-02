import re
from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Älvsbyns Energi"
DESCRIPTION = "Waste collection schedule for Älvsbyns Energi, Sweden."
URL = "https://www.alvsbynsenergi.se/"
COUNTRY = "se"

TEST_CASES = {
    "Storgatan 24": {
        "address": "Storgatan 24",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address and house number.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the street address and house number as shown by the address "
    "search at https://www.alvsbynsenergi.se/ (for example, Storgatan 24).",
}

ICON_MAP = {
    "Matavfall": Icons.BIO_KITCHEN,
    "Restavfall": Icons.GENERAL_WASTE,
}

BASE_URL = "https://www.alvsbynsenergi.se"
ADDRESS_URL = f"{BASE_URL}/assets/data/ajax.fetch_address.php"
SCHEDULE_URL = f"{BASE_URL}/renhallning/sophamtning/{{street_id}}-{{area_code}}"
DATE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _normalise(value: str) -> str:
    return " ".join(value.split()).casefold()


class Source:
    def __init__(self, address: str):
        self._address = (address or "").strip()
        if not self._address:
            raise SourceArgumentRequired(
                "address",
                "A street address and house number are required.",
            )

    def fetch(self) -> list[Collection]:
        response = requests.get(
            ADDRESS_URL,
            params={"query": self._address},
            timeout=30,
        )
        response.raise_for_status()

        suggestions = response.json().get("suggestions", [])
        normalised_address = _normalise(self._address)
        matches = [
            suggestion
            for suggestion in suggestions
            if _normalise(suggestion.get("value", "")).startswith(normalised_address)
        ]

        if len(matches) != 1:
            suggestion_values = sorted(
                suggestion.get("value", "").strip()
                for suggestion in suggestions
                if suggestion.get("value", "").strip()
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                suggestion_values,
            )

        street_id = matches[0].get("street_id")
        area_code = matches[0].get("area_code")
        if not street_id or not area_code:
            raise ValueError("Unexpected address response from Älvsbyns Energi.")

        response = requests.get(
            SCHEDULE_URL.format(
                street_id=street_id,
                area_code=area_code,
            ),
            timeout=30,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        details = soup.select_one("#waste-empty-details")
        if details is None:
            raise ValueError(
                "Collection schedule was not found in the Älvsbyns Energi response."
            )

        entries = []
        for item in details.find_all("span", recursive=False):
            text = item.get_text(" ", strip=True)
            match = DATE_PATTERN.match(text)
            if match is None:
                continue

            collection_date = date.fromisoformat(match.group(1))

            entries.append(
                Collection(
                    date=collection_date,
                    t="Matavfall",
                    icon=ICON_MAP["Matavfall"],
                )
            )

            if "matavfall" not in text.casefold():
                entries.append(
                    Collection(
                        date=collection_date,
                        t="Restavfall",
                        icon=ICON_MAP["Restavfall"],
                    )
                )

        if not entries:
            raise ValueError(
                "No collection dates were found in the Älvsbyns Energi response."
            )

        return entries
