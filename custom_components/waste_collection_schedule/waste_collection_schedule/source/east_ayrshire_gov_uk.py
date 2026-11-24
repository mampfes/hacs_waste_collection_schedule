from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "East Ayrshire Council"
DESCRIPTION = "Source for east-ayrshire.gov.uk services for East Ayrshire"
URL = "https://www.east-ayrshire.gov.uk/"
COUNTRY = "uk"

TEST_CASES = {
    "Church Hall, Stewarton": {"address": "Church Hall Lainshaw Street"},
    "Village Hall, Drongan": {"address": "Village Hall Littlemill Road"},
    "Church Hall, Mauchline (picked suggestion)": {
        "address": "Church Hall Loudoun Street, Mauchline, KA5 5BZ"
    },
}

# The council's bin collection days page embeds Routeware's ReCollect widget
# (area "EastAyrshireUK"). The address lookup and the collection events come
# from the ReCollect API.
API_BASE = "https://api.eu.recollect.net/api"
AREA_URL = f"{API_BASE}/areas/EastAyrshireUK/services/waste"

# The food caddy goes out with every bin, so the ReCollect labels "<bin>+Food"
# are split into the bin and "Food Waste".
TYPE_MAP = {
    "General Waste+Food (+food only after transition week)": [
        "General Waste",
        "Food Waste",
    ],
    "Trolley+Food": ["Recycling Trolley", "Food Waste"],
    "Paper/Card+Food": ["Paper/Card", "Food Waste"],
    "Plastic/Cans+Food": ["Plastic/Cans", "Food Waste"],
    "Glass+Food": ["Glass", "Food Waste"],
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Food Waste": Icons.BIO_KITCHEN,
    "Recycling Trolley": Icons.RECYCLING,
    "Paper/Card": Icons.PAPER,
    "Plastic/Cans": Icons.RECYCLING,
    "Glass": Icons.GLASS,
    "Garden Waste": Icons.GARDEN,
    "Transition Week": Icons.EVENT,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://www.east-ayrshire.gov.uk/Housing/RubbishAndRecycling/Collection-days/bin-collection-days.aspx and type your address into the search to see the exact wording, then use the same here. House number and street (e.g. '1 Main Street') or a property name work. A postcode usually covers several properties, so add the house number or name.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your address as entered on the East Ayrshire Council bin collection days search (house number and street, or property name)",
        "uprn": "No longer used. The council's new bin calendar cannot be searched by UPRN, use address instead.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
        "uprn": "UPRN (no longer used)",
    },
}


def _normalise_address(address: str) -> str:
    return " ".join(str(address).split()).casefold()


def _waste_types(subject: str) -> list[str]:
    if subject in TYPE_MAP:
        return TYPE_MAP[subject]
    if subject.endswith("+Food"):
        return [subject.removesuffix("+Food").strip(), "Food Waste"]
    return [subject]


class Source:
    def __init__(self, address: str | None = None, uprn: str | int | None = None):
        # `uprn` is only accepted so that configurations created for the old
        # calendar still load and get a helpful message instead of a TypeError.
        self._address = address
        self._uprn = uprn

    @staticmethod
    def _suggest(query: str) -> list[dict]:
        response = requests.get(
            f"{AREA_URL}/address-suggest",
            params={"q": query, "locale": "en-GB"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def _resolve_place_id(self, address: str) -> str:
        """Resolve the configured address to a ReCollect place ID."""
        suggestions = self._suggest(address)

        # The search finds nothing for its own full labels, such as
        # "Church Hall Loudoun Street, Mauchline, KA5 5BZ", so drop trailing
        # parts until it does.
        parts = [part.strip() for part in address.split(",")]
        shortened = False
        while not suggestions and len(parts) > 1:
            parts.pop()
            shortened = True
            suggestions = self._suggest(", ".join(parts))

        if not suggestions:
            raise SourceArgumentNotFound("address", address)

        wanted = _normalise_address(address)
        exact = [s for s in suggestions if _normalise_address(s["name"]) == wanted]
        if len(exact) == 1:
            suggestions = exact
        elif len(suggestions) > 1 or shortened:
            # A shortened search ignored part of the input, so even a single
            # result is offered for confirmation rather than used.
            raise SourceArgAmbiguousWithSuggestions(
                "address", address, [s["name"] for s in suggestions]
            )

        suggestion = suggestions[0]
        if suggestion.get("type") != "parcel" or "place_id" not in suggestion:
            # A postcode returns a "place_qualifier", which needs a more
            # specific address to resolve to a single property.
            raise SourceArgumentNotFound(
                "address",
                address,
                "this looks like a postcode with several properties, please add your house number or property name.",
            )
        return suggestion["place_id"]

    def fetch(self) -> list[Collection]:
        if not self._address:
            reason = "please configure your address as shown by the council's bin collection days search"
            if self._uprn is not None:
                reason = (
                    "the council's new bin calendar cannot be searched by UPRN any more, "
                    + reason
                )
            raise SourceArgumentRequired("address", reason)

        address = str(self._address)
        place_id = self._resolve_place_id(address)

        response = requests.get(
            f"{API_BASE}/places/{place_id}/services/waste/events",
            params={
                "hide": "reminder_only",
                "after": (date.today() - timedelta(days=30)).isoformat(),
                "before": (date.today() + timedelta(days=365)).isoformat(),
                "locale": "en-GB",
            },
            timeout=30,
        )
        if response.status_code == 404:
            # Some properties (e.g. community centres) are in the address
            # search but have no council bin collections.
            raise SourceArgumentNotFound(
                "address",
                address,
                "the council has no bin collections for this property.",
            )
        response.raise_for_status()
        events = response.json().get("events", [])

        entries: list[Collection] = []
        seen: set[tuple[date, str]] = set()
        for event in events:
            collection_date = date.fromisoformat(event["day"])
            for flag in event.get("flags", []):
                # Skip non-pickup flags (e.g. holiday notices) so they don't
                # surface as bogus collection types.
                if flag.get("event_type") != "pickup":
                    continue
                subject = flag.get("subject") or flag.get("name")
                if not subject:
                    continue
                for waste_type in _waste_types(subject):
                    if (collection_date, waste_type) in seen:
                        continue
                    seen.add((collection_date, waste_type))
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )
        return entries
