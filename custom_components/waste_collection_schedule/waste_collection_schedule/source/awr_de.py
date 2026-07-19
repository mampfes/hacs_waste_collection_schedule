"""Abfallwirtschaft Rendsburg (awr.de).

Not a TwoStepRetriever shape: resolving the final calendar URL takes three
sequential lookups (city -> id, then street -> id scoped to that city, then
the city's active waste-type ids), not one lookup + one schedule fetch. A
source-defined ``retrieve`` covers the whole chain.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

BASE_URL = "https://www.awr.de"

# Event summaries carry a container-size/frequency annotation the legacy
# source displayed verbatim (e.g. "Restabfall ab 770L(2-wöchentlich)",
# "Bioabfall(14-täglich)"). Stripping it exposes the plain waste-type name so
# the shared multilingual vocabulary can resolve it; a label that doesn't fit
# this shape passes through untouched and is preserved verbatim as before.
_TRAILING_PARENTHETICAL = re.compile(r"\s*\([^)]*\)\s*$")
_TRAILING_BIN_SIZE = re.compile(r"\s+ab\s+\d+\s*l\b.*$", re.IGNORECASE)


def _clean(label: str) -> str:
    label = _TRAILING_PARENTHETICAL.sub("", label)
    label = _TRAILING_BIN_SIZE.sub("", label)
    return label.strip()


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Rendsburg"
    DESCRIPTION = "Source for Abfallwirtschaft Rendsburg"
    URL = "https://www.awr.de"
    COUNTRY = "de"
    # Canonical types observed in the calendar feed; the cleaned German labels
    # resolve through the shared multilingual vocabulary.
    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rendsburg": {"city": "Rendsburg", "street": "Hindenburgstraße"},
    }

    PARAMS = (city(), street())
    RAISE_ON_EMPTY = True

    parse = IcsParser()
    transform = ICSTransformer(clean=_clean)

    def retrieve(self, source):
        city_name = source.params["city"]
        street_name = source.params["street"]

        cities_response = source.session.get(
            f"{BASE_URL}/api_v2/collection_dates/1/orte"
        )
        cities_response.raise_for_status()
        cities = cities_response.json()
        city_to_id = {
            entry["ortsbezeichnung"]: entry["ortsnummer"] for entry in cities["orte"]
        }
        if city_name not in city_to_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", city_name, city_to_id.keys()
            )
        city_id = city_to_id[city_name]

        streets_response = source.session.get(
            f"{BASE_URL}/api_v2/collection_dates/1/ort/{city_id}/strassen"
        )
        streets_response.raise_for_status()
        streets = streets_response.json()
        street_to_id = {
            entry["strassenbezeichnung"]: entry["strassennummer"]
            for entry in streets["strassen"]
        }
        if street_name not in street_to_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street_name, street_to_id.keys()
            )
        street_id = street_to_id[street_name]

        waste_types_response = source.session.get(
            f"{BASE_URL}/api_v2/collection_dates/1/ort/{city_id}/abfallarten"
        )
        waste_types_response.raise_for_status()
        waste_types = waste_types_response.json()
        waste_type_ids = "-".join(entry["id"] for entry in waste_types["abfallarten"])

        return source.session.get(
            f"{BASE_URL}/api_v2/collection_dates/1/ort/{city_id}/strasse/"
            f"{street_id}/hausnummern/0/abfallarten/{waste_type_ids}/kalender.ics"
        )

    def __init__(self, city: str, street: str):
        super().__init__(city=city, street=street)
