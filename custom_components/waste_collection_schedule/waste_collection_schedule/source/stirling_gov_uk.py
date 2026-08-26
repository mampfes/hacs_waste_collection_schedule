from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

TITLE = "Stirling Council"
DESCRIPTION = "Source for Stirling Council waste collection services."
URL = "https://www.stirling.gov.uk/"
TEST_CASES = {
    "Kildean Road 38": {"address": "38 Kildean Road"},
    "Merlo Buchanan Castle Estate": {"address": "Merlo"},
}

# Stirling Council uses Routeware's ReCollect platform (area "StirlingUK").
# The address lookup and collection events are provided by the ReCollect API.
API_URL = "https://api.eu.recollect.net/api/areas/StirlingUK/services/waste"

# Waste types returned by Stirling's ReCollect service (flag name -> icon).
ICON_MAP = {
    "REFUSE": Icons.GENERAL_WASTE,
    "GARDEN": Icons.ORGANIC,
    "RECYCLING": Icons.PAPER,
    "PLASTIC": Icons.RECYCLING,
    "GLASS": Icons.GLASS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://www.stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/ and type your address into the search to see the exact wording, then use the same here. House number and street (e.g. '38 Kildean Road'), property name (e.g. 'Merlo'), or a single-dwelling postcode work.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your address as entered on the Stirling Council bin collection dates search (house number and street, property name, or single-dwelling postcode)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"address": "Address"},
}

SOURCE_CODEOWNERS = ["@nagug"]


class Source:
    def __init__(self, address: str):
        self._address = address

    def _resolve_place_id(self) -> str:
        """Resolve the configured address to a ReCollect place ID."""
        response = requests.get(
            f"{API_URL}/address-suggest",
            params={"q": self._address, "locale": "en-GB"},
            timeout=30,
        )
        response.raise_for_status()
        suggestions = response.json()

        if not suggestions:
            raise SourceArgumentNotFound("address", self._address)

        if len(suggestions) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address", self._address, [s["name"] for s in suggestions]
            )

        suggestion = suggestions[0]
        if suggestion.get("type") != "parcel" or "place_id" not in suggestion:
            # Multi-dwelling postcodes return a "place_qualifier" which needs a
            # more specific address to resolve to a single property.
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "this looks like a multi-dwelling postcode, please add your house number or property name.",
            )
        return suggestion["place_id"]

    def fetch(self) -> list[Collection]:
        place_id = self._resolve_place_id()

        response = requests.get(
            f"https://api.eu.recollect.net/api/places/{place_id}/services/waste/events",
            params={
                "hide": "reminder_only",
                "after": (date.today() - timedelta(days=30)).isoformat(),
                "before": (date.today() + timedelta(days=365)).isoformat(),
                "locale": "en-GB",
            },
            timeout=30,
        )
        response.raise_for_status()
        events = response.json().get("events", [])

        entries = []
        for event in events:
            collection_date = date.fromisoformat(event["day"])
            for flag in event.get("flags", []):
                # Skip non-pickup flags (e.g. holiday notices) so they don't
                # surface as bogus collection types.
                if flag.get("event_type") != "pickup":
                    continue
                waste_type = flag.get("subject") or flag.get("name")
                if not waste_type:
                    continue
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(flag.get("name")),
                    )
                )
        return entries
