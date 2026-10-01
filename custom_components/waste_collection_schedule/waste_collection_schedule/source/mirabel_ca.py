from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import area_id
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

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

# The API zone ids differ a bit from the official zone numbers.
_ZONE_IDS = {
    "1": 121,
    "2": 122,
    "3": 123,
    "4": 124,
    "5": 125,
    "6": 126,
    "7": 127,
    "8": 128,
}


def _zone_id(zone, **_) -> int:
    key = str(zone).strip()
    if key not in _ZONE_IDS:
        raise SourceArgumentNotFoundWithSuggestions(
            "zone", zone, suggestions=list(_ZONE_IDS)
        )
    return _ZONE_IDS[key]


@final
class Source(BaseSource):
    TITLE = "Mirabel (QC)"
    DESCRIPTION = "Source script for mirabel.ca/collectes"
    URL = "https://mirabel.ca/collectes"
    COUNTRY = "ca"

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Mirabel-en-Haut": {"zone": 1},
        "Saint-Antoine": {"zone": 2},
        "Sainte-Monique": {"zone": 3},
        "Domaine-Vert Nord": {"zone": 4},
        "Saint-Janvier": {"zone": 5},
        "Saint-Augustin": {"zone": 6},
        "Saint-Canut": {"zone": 7},
        "St-Benoit": {"zone": 8},
    }

    PARAMS = (area_id("zone"),)

    HOWTO: ClassVar[dict] = {
        "en": "You can find your collection zone number (1 to 8) using the webpage: https://mirabel.ca/services/services-en-ligne/trouver-ma-zone-de-collecte",
        "fr": "Vous pouvez trouver votre numéro de zone de collecte (1 à 8) sur l'adresse suivante : https://mirabel.ca/services/services-en-ligne/trouver-ma-zone-de-collecte",
    }

    retrieve = retrievers.HttpPostRetriever(
        "https://mviv2.mirabel.ca/graphql",
        json=lambda zone, **_: {
            "query": EVENT_QUERY,
            "variables": {"zoneId": _zone_id(zone)},
        },
        timeout=15,
    )

    parse = parsers.JsonParser("data", "events", "nodes")

    transform = JsonTransformer(
        date_key="date",
        type_key=lambda event: event["type"]["slug"],
        type_value_map={
            "dechets": wt.GENERAL_WASTE,
            "recyclage": wt.RECYCLABLES,
            "composte": wt.ORGANIC,  # codespell:ignore composte
            "encombrants": wt.BULKY_WASTE,
        },
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
