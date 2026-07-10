"""Source for Hemar (ichisystem.eu), Poland."""

from datetime import date
from typing import List

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.Sepan import SepanClient

TITLE = "Hemar (ichisystem.eu)"
DESCRIPTION = (
    "Source for the Hemar waste collection schedule platform "
    "(harmonogram.ichisystem.eu) used by several Polish municipalities. "
    'This deployment runs on the same underlying "SEPAN"/ICHI System '
    "platform as sepan_remondis_pl, zys_harmonogram_pl and alba_com_pl."
)
URL = "https://harmonogram.ichisystem.eu/hemar/"
COUNTRY = "pl"

TEST_CASES = {
    "Pobiedziska, Boczna 2": {
        "city": "Pobiedziska",
        "street": "Boczna",
        "house_number": "2",
    },
    "Pobiedziska, Dworcowa 1": {
        "city": "POBIEDZISKA",
        "street": "DWORCOWA",
        "house_number": "1",
    },
}

EXTRA_INFO = [
    {
        "title": "Pobiedziska",
        "url": "https://harmonogram.ichisystem.eu/hemar/",
        "default_params": {"city": "Pobiedziska"},
    },
    {
        "title": "Kiszkowo",
        "url": "https://harmonogram.ichisystem.eu/hemar/",
        "default_params": {"city": "Kiszkowo"},
    },
]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://harmonogram.ichisystem.eu/hemar/ and pick your city, "
        "street, and house number from the dropdowns. Use those exact values "
        "for the city, street, and house_number arguments (matching is "
        "case-insensitive)."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "City / town name as listed on the Hemar portal.",
        "street": "Street name as listed on the Hemar portal.",
        "house_number": "House number as listed on the Hemar portal.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
        "house_number": "House number",
    },
}

# Waste-type names as rendered by this deployment's report table (matches
# the wording used by the alba_com_pl / zys_harmonogram_pl deployments of
# the same underlying platform).
ICON_MAP = {
    "Zmieszane odpady komunalne": Icons.GENERAL_WASTE,
    "Metale i tworzywa sztuczne": Icons.RECYCLING,
    "Papier": Icons.PAPER,
    "Szkło": Icons.GLASS,
    "Bioodpady": Icons.ORGANIC,
    "Bioodpady - Drzewka świąteczne": Icons.CHRISTMAS_TREE,
    "Odpady wystawkowe": Icons.BULKY,
}

API_BASE = "https://harmonogram.ichisystem.eu/hemar"


class Source:
    def __init__(self, city: str, street: str, house_number: str):
        self._client = SepanClient([API_BASE])
        self._address_id = self._client.resolve_address(city, street, house_number)

    def fetch(self) -> List[Collection]:
        entries = self._client.fetch_schedule(self._address_id)
        today = date.today()
        return [
            Collection(
                date=collection_date, t=waste_type, icon=ICON_MAP.get(waste_type)
            )
            for collection_date, waste_type in entries
            # Skip dates more than 30 days in the past to keep payload small.
            if (today - collection_date).days <= 30
        ]
