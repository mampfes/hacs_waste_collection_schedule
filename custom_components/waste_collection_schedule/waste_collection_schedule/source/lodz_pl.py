import json
import logging
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Łódź"
DESCRIPTION = "Source for Łódź city garbage collection"
URL = "https://kartalodzianina.pl"
TEST_CASES = {
    "Podchorążych 1 (Letniskowa)": {
        "street": "Podchorążych",
        "house_number": "1",
        "building_type": 3,
    },
    "Piotrkowska 104 (Wielorodzinna)": {
        "street": "Piotrkowska",
        "house_number": "104",
        "building_type": 2,
    },
    "Partyzantów 1 (Jednorodzinna)": {
        "street": "Partyzantów",
        "house_number": "1",
        "building_type": 1,
    },
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Szkło": "mdi:glass-fragile",
    "Papier": "mdi:package-variant",
    "Metale i tworzywa sztuczne": "mdi:recycle",
    "Resztkowe": "mdi:trash-can",
    "Mokre Bio": "mdi:leaf",
}


class Source:
    def __init__(self, street: str, house_number: str, building_type: int = 1):
        """Initialize the source.

        :param street: Street name (e.g., "Adwentowicza")
        :param house_number: House number (e.g., "1", "2a")
        :param building_type: Building type: 1 (single-family), 2 (multi-family), 3 (summer house). Default is 1.
        """
        self.street = street
        self.house_number = str(house_number)
        self.building_type = building_type

    def fetch(self) -> list[Collection]:
        # Validate required arguments
        if not self.street:
            raise SourceArgumentRequired("street", "A street name is required")
        if not self.house_number:
            raise SourceArgumentRequired("house_number", "A house number is required")
        if str(self.building_type) not in ["1", "2", "3"]:
            raise SourceArgumentException(
                "building_type",
                f"Invalid value '{self.building_type}': Must be 1 (single-family), 2 (multi-family), or 3 (summer house).",
            )

        # GET request parameters for the Karta Łodzianina API
        params: dict[str, str | int] = {
            "iframe": "",
            "actionPerformedWyszukajTyp": "",
            "odpad": "",
            "ulica": self.street,
            "nrDomu": self.house_number,
            "idMiejscowosci": "undefined",
            "rodzajZabudowy": self.building_type,
        }

        try:
            response = requests.get(f"{URL}/wywoz-odpadow", params=params, timeout=30)
            response.raise_for_status()
            html_content = response.text
        except requests.RequestException as e:
            raise ValueError(f"Error fetching data from Łódź API: {e}") from e

        # Check if the address exists in the database
        if "Brak dostępnego harmonogramu dla wskazanego adresu" in html_content:
            # Raise predefined custom exception with details
            raise SourceArgumentNotFound(
                "street/house_number/building_type",
                f"{self.street} {self.house_number} ({self.building_type})",
            )

        # Extracting the JSON array hidden in the JavaScript code (FullCalendar library)
        # Using re.DOTALL so the regex works across multiple lines
        pattern = r"events:\s*(\[.*?\])\s*,\s*eventDidMount"
        match = re.search(pattern, html_content, re.DOTALL)

        if not match:
            raise SourceArgumentNotFound(
                "Page retrieved, but calendar data (JSON) was not found."
            )

        json_data = match.group(1)

        try:
            events = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing the JSON schedule: {e}")

        entries = []

        # Iterate over each extracted event
        for event in events:
            waste_type = event.get("title")
            date_str = event.get("start")

            if not waste_type or not date_str:
                continue

            try:
                # The date format in JSON is always YYYY-MM-DD
                event_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                entries.append(
                    Collection(
                        date=event_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                    )
                )
            except ValueError:
                _LOGGER.warning(f"Ignored invalid date format: {date_str}")

        if not entries:
            raise SourceArgumentExceptionMultiple(
                ["street", "house_number", "building_type"],
                f"No collection dates found for {self.street} {self.house_number} ({self.building_type}) (calendar returned no usable events).",
            )
        return entries
