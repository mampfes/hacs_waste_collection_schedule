import logging
import re
from datetime import date, datetime

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

_LOGGER = logging.getLogger(__name__)

TITLE = "Kungälvs kommun Avfallshantering"
DESCRIPTION = "Source script for kungalv.se"
URL = "https://www.kungalv.se/Bygga--bo--miljo/avfall-och-atervinning/avfall-fran-hushall/"
TEST_CASES = {
    "Komministergatan": {"street_address": "Komministergatan 4, Kungälv"},
    "Violgatan": {"street_address": "Violgatan 8, Ytterby"},
    "Slam": {"street_address": "Ödsmål 110, Kode"},
}

API_URL = "https://minasidor-va-avfall.kungalv.se/FutureWeb/SimpleWastePickup"

ICON_MAP = {
    "Restavfall": Icons.GENERAL_WASTE,
    "Matavfall": Icons.BIO_KITCHEN,
    "Förpackningar": Icons.PAPER,
    "Metallförp.": Icons.METAL,
}

# Swedish month abbreviations used by the FutureWeb API when only a month is
# known for the next pickup (e.g. seasonal services like "Slam"/"Fett"),
# instead of an exact date.
MONTH_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "maj": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "dec": 12,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Street address for waste collection, including city.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street address",
    },
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        # Search for address
        response = requests.post(
            f"{API_URL}/SearchAdress",
            data={"searchText": self._street_address},
            timeout=30,
        )
        response.raise_for_status()

        address_data = response.json()
        if not address_data.get("Succeeded") or not address_data.get("Buildings"):
            raise SourceArgumentNotFound("street_address", self._street_address)

        # Extract building ID from first result (format: "Address, CITY (ID)")
        building = address_data["Buildings"][0]
        match = re.search(r"\((\d+)\)", building)
        if not match:
            raise SourceArgumentNotFound("street_address", self._street_address)

        building_id = match.group(1)

        # Get waste pickup schedule
        response = requests.get(
            f"{API_URL}/GetWastePickupSchedule",
            params={"address": f"({building_id})"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        entries = []
        for item in data.get("RhServices", []):
            next_pickup = item.get("NextWastePickup")
            if not next_pickup:
                continue

            waste_type = item.get("WasteType", "")
            next_pickup_date = self._parse_pickup_date(next_pickup)
            if next_pickup_date is None:
                _LOGGER.warning(
                    "Failed to parse pickup date '%s' for waste type '%s', skipping entry",
                    next_pickup,
                    waste_type,
                )
                continue

            entries.append(
                Collection(
                    date=next_pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, Icons.GENERAL_WASTE),
                )
            )

        return entries

    @staticmethod
    def _parse_pickup_date(next_pickup: str) -> date | None:
        # Regular pickups are returned as an exact date, e.g. "2026-09-24".
        try:
            return datetime.strptime(next_pickup, "%Y-%m-%d").date()
        except ValueError:
            pass

        # Seasonal services (e.g. "Slam"/"Fett") that don't yet have an exact
        # pickup date are returned as a Swedish month abbreviation and year
        # instead, e.g. "Jan 2027" or "Maj 2027". Fall back to the first of
        # that month to at least get something close, rather than failing
        # the whole update.
        parts = next_pickup.split()
        if len(parts) == 2:
            month_name, year_str = parts
            month = MONTH_MAP.get(month_name.strip().lower())
            if month and year_str.isdigit():
                return date(int(year_str), month, 1)

        return None
