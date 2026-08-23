from datetime import datetime
from typing import Literal, TypedDict

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions


class Zone(TypedDict):
    id: int


TITLE = "Mirabel (QC)"
DESCRIPTION = "Source script for mirabel.ca/collectes"
URL = "https://mirabel.ca/collectes"
COUNTRY = "ca"

TEST_CASES = {
    "Mirabel-en-Haut": {"zone": 1},
    "Saint-Antoine": {"zone": 2},
    "Sainte-Monique": {"zone": 3},
    "Domaine-Vert Nord": {"zone": 4},
    "Saint-Janvier": {"zone": 5},
    "Saint-Augustin": {"zone": 6},
    "Saint-Canut": {"zone": 7},
    "St-Benoit": {"zone": 8},
}


EVENT_QUERY = """
query eventTypes($month: Int, $year: Int, $zoneId: Int) {
    events(year: $year, month: $month, zoneId: $zoneId) {
        nodes {
            date
            id
            type {
                color
                id
                text: name
                slug
                __typename
            }
            zone {
                id
                name
                slug
                __typename
            }
            __typename
        }
    __typename
    }
}
"""

API_URL = "https://mviv2.mirabel.ca/graphql"


ICON_MAP = {
    "dechets": Icons.GENERAL_WASTE,
    "recyclage": Icons.RECYCLING,
    "composte": Icons.ORGANIC,  # codespell:ignore composte
    "encombrants": Icons.BULKY,
}


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your collection zone number using the webpage: https://mirabel.ca/services/services-en-ligne/trouver-ma-zone-de-collecte",
    "fr": "Vous pouvez trouver votre numéro de zone de collecte sur l'adresse suivante : https://mirabel.ca/services/services-en-ligne/trouver-ma-zone-de-collecte",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "zone": "Collection zone number",
    },
    "fr": {
        "zone": "Numéro de la zone de collecte",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "zone": "Collection zone number",
    },
    "fr": {
        "zone": "Zone de collecte",
    },
}

# The id differ a bit from the zone official zone number.
_ZONE_INFO = {
    "1": 121,
    "2": 122,
    "3": 123,
    "4": 124,
    "5": 125,
    "6": 126,
    "7": 127,
    "8": 128,
}

ZONE_LITERALS = Literal[tuple(_ZONE_INFO.keys())]

ZONES: dict[str, Zone] = {name: {"id": zid} for name, zid in _ZONE_INFO.items()}


class Source:
    def __init__(self, zone: ZONE_LITERALS):  # type: ignore
        zone = str(zone)
        if zone not in ZONES:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone", zone, suggestions=ZONES.keys()
            )
        self._id = ZONES[zone]["id"]

    def fetch(self) -> list[Collection]:

        entries = []

        with requests.Session() as session:
            session.headers.update({"Content-Type": "application/json"})
            r = session.post(
                API_URL,
                json={
                    "query": EVENT_QUERY,
                    "variables": {"zoneId": self._id},
                },
                timeout=15,
            )
            try:
                r.raise_for_status()
            except requests.HTTPError as e:
                raise RuntimeError(
                    f"Failed to fetch collections for zone '{self._id}': {e}"
                ) from e

            payload = r.json()
            if "errors" in payload:
                raise RuntimeError(f"GraphQL errors: {payload['errors']}")

            events = payload.get("data", {}).get("events", {}).get("nodes") or []
            for event in events:
                event_type = event.get("type")
                entries.append(
                    Collection(
                        date=datetime.fromisoformat(event.get("date")).date(),
                        t=event_type.get("text"),
                        icon=ICON_MAP.get(event_type.get("slug")),
                    )
                )

        return entries
