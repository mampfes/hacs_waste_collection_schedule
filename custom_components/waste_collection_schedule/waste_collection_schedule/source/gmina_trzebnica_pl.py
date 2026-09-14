import datetime
import logging

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Gmina Trzebnica"
DESCRIPTION = "Source for Gmina Trzebnica, Poland (SkyCMS municipal app API)"
URL = "https://trzebnica.pl"
COUNTRY = "pl"

TEST_CASES = {
    "Trzebnica - Brzyków (Sołectwa 8)": {"region_id": 88},
    "Trzebnica 2": {"region_id": 8},
}

SOURCE_CODEOWNERS = ["@Tymon3310"]

API_BASE = "https://api.skycms.com.pl/api/v1/rest"
# Public API key of the "Gmina Trzebnica" SkyCMS app. It identifies the
# municipality (tenant), not a user, and is shipped with the public app.
# Other SkyCMS municipalities use their own key and their own region IDs,
# so this source is scoped to Gmina Trzebnica.
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

ICON_MAP = {
    "Odpady Zielone / Kuchenne": Icons.ORGANIC,
    "Odpady Zielone": Icons.GARDEN,
    "Wielkogabarytowe": Icons.BULKY,
    "Tworzywa sztuczne": Icons.PLASTIC_PACKAGING,
    "Zmieszane": Icons.GENERAL_WASTE,
    "Papier": Icons.PAPER,
    "Szkło": Icons.GLASS,
    "Bio": Icons.ORGANIC,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Install the 'Gmina Trzebnica' app and look up your waste collection region. The region ID can be found in the app's waste calendar section, or in the region list linked from the documentation of this source.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "region_id": "Waste collection region ID of the Gmina Trzebnica SkyCMS app",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "region_id": "Region ID",
    },
}


def _get_icon(waste_name: str) -> Icons | None:
    """Return the icon matching a waste type name.

    Keys are matched longest-first so that a more specific waste type
    (e.g. "Odpady Zielone / Kuchenne") is never shadowed by a shorter key
    that happens to be a substring of it (e.g. "Odpady Zielone").
    """
    name = waste_name.lower()
    for key in sorted(ICON_MAP, key=len, reverse=True):
        if key.lower() in name:
            return ICON_MAP[key]
    return None


class Source:
    def __init__(self, region_id):
        try:
            self._region_id = int(region_id)
        except (ValueError, TypeError) as e:
            raise SourceArgumentNotFound(
                "region_id", region_id, "it must be a numeric region ID."
            ) from e

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        response = session.get(
            f"{API_BASE}/garbage/disposals/{self._region_id}", timeout=30
        )
        response.raise_for_status()

        data = response.json().get("data") or {}
        # Unknown region IDs still return HTTP 200 with success=true, but the
        # payload only contains a message instead of the schedule.
        if "garbage_kinds" not in data:
            raise SourceArgumentNotFoundWithSuggestions(
                "region_id", self._region_id, self._fetch_region_ids(session)
            )

        entries: list[Collection] = []

        for waste in data["garbage_kinds"] or []:
            waste_name = waste["name"]
            icon = _get_icon(waste_name)

            for disposal in waste.get("disposals", []):
                try:
                    pickup_date = datetime.date.fromisoformat(disposal["id"])
                except ValueError:
                    _LOGGER.warning("Invalid date: %s", disposal["id"])
                    continue
                entries.append(Collection(pickup_date, waste_name, icon=icon))

        return entries

    @staticmethod
    def _fetch_region_ids(session: requests.Session) -> list[int]:
        """Return all region IDs known to the app, used as error suggestions."""
        try:
            response = session.get(f"{API_BASE}/garbage/regions", timeout=30)
            response.raise_for_status()
            regions = (response.json().get("data") or {}).get("regions") or []
        except (requests.RequestException, ValueError):
            return []
        return [region["id"] for region in regions if "id" in region]
