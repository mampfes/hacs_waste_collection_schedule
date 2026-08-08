import datetime
import logging

import requests

from ..collection import Collection
from ..exceptions import SourceArgumentNotFound
from ..icons import Icons

_LOGGER = logging.getLogger(__name__)

TITLE = "Gmina Trzebnica (SkyCMS)"
DESCRIPTION = "Source for Gmina Trzebnica waste collection schedules via SkyCMS API"
URL = "https://api.skycms.com.pl"
COUNTRY = "pl"

TEST_CASES = {
    "Trzebnica - Brzyków (Sołectwa 8)": {"region_id": 88},
    "Trzebnica 2": {"region_id": 8},
}

API_BASE = "https://api.skycms.com.pl/api/v1/rest"
# Public API key shipped with the SkyCMS mobile app (extracted from APK).
# Not a user-specific secret; same key is embedded in every SkyCMS client.
API_KEY = "a90a376c6b19307acf1334b1a3937235"

HEADERS = {
    "x-skycms-key": API_KEY,
    "x-skycms-device": "waste-collection-schedule",
    "x-skycms-type": "web",
    "x-skycms-model": "waste-collection-schedule",
    "x-skycms-version": "1.0.0",
    "x-skycms-app-version": "1.0.0",
    "x-skycms-language": "pl",
}

# Sorted longest-first so substring matches don't shadow longer keys
ICON_MAP = {
    "Odpady Zielone / Kuchenne": Icons.BIO_KITCHEN,
    "Odpady Zielone": Icons.GARDEN,
    "Wielkogabarytowe": Icons.BULKY,
    "Tworzywa sztuczne": Icons.PLASTIC_PACKAGING,
    "Zmieszane": Icons.GENERAL_WASTE,
    "Papier": Icons.PAPER,
    "Szkło": Icons.GLASS,
    "Bio": Icons.BIO_KITCHEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Install the 'Gmina Trzebnica' app (or another SkyCMS-powered municipal app) and look up your waste collection region. The region ID can be found in the app's waste calendar section.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "region_id": "Waste collection region ID from the SkyCMS API",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "region_id": "Region ID",
    },
}


class Source:
    def __init__(self, region_id):
        try:
            self._region_id = int(region_id)
        except (ValueError, TypeError) as e:
            raise SourceArgumentNotFound(
                f"Invalid region_id: {region_id!r}. Must be a numeric ID."
            ) from e

    def fetch(self):
        session = requests.Session()
        session.headers.update(HEADERS)

        url = f"{API_BASE}/garbage/disposals/{self._region_id}"
        response = session.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        if not data.get("success"):
            raise SourceArgumentNotFound(
                f"Region ID {self._region_id} not found or has no schedule data"
            )

        garbage_kinds = data["data"].get("garbage_kinds", [])
        entries = []

        for waste in garbage_kinds:
            waste_name = waste["name"]
            icon = None
            for key, val in ICON_MAP.items():
                if key.lower() in waste_name.lower():
                    icon = val
                    break

            for disposal in waste.get("disposals", []):
                try:
                    pickup_date = datetime.date.fromisoformat(disposal["id"])
                except ValueError:
                    _LOGGER.warning("Invalid date: %s", disposal["id"])
                    continue
                entries.append(Collection(pickup_date, waste_name, icon=icon))

        return entries
