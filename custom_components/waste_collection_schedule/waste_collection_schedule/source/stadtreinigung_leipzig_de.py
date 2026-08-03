"""Stadtreinigung Leipzig.

A two-step address lookup (a street/house-number search resolves an opaque
position id) feeding a single ICS download, which is the shared
``LookupChainRetriever``: the lookup step below resolves the id and the
retriever fetches the calendar with it.
"""

import json
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_STREETS_URL = "https://stadtreinigung-leipzig.de/rest/Navision/Streets"
_ICS_URL = (
    "https://stadtreinigung-leipzig.de/wir-kommen-zu-ihnen/abfallkalender/ical.ics"
)

# The feed labels bins "<bin> (Abholzeit)" (and sometimes a trailing ", "), which
# the shared vocabulary does not match. Drop the parenthetical and reduce the
# label to its core bin term for the type_value_map.
_TYPE_VALUE_MAP = {
    "biotonne": ORGANIC,
    "gelbe tonne": RECYCLABLES,
    "blaue tonne": PAPER,
    "restabfall": GENERAL_WASTE,
}


def _clean(label: str) -> str:
    text = label.split("(")[0].strip().rstrip(",").strip().lower()
    if "biotonne" in text or "bioabfall" in text:
        return "biotonne"
    if "gelbe" in text or "wertstoff" in text:
        return "gelbe tonne"
    if "blaue" in text or "papier" in text:
        return "blaue tonne"
    if "restabfall" in text or "restmüll" in text:
        return "restabfall"
    return label


def _resolve_position(source: BaseSource, keys: tuple) -> str:
    """Resolve the street and house number to the feed's opaque position id."""
    street_name = source.params["street"]
    house_number_value = source.params["house_number"]

    params = {"old_format": 1, "search": street_name}
    r = source.session.get(_STREETS_URL, params=params)

    data = json.loads(r.text)
    if len(data["results"]) == 0:
        raise SourceArgumentNotFound("street", street_name)
    street_entry = data["results"].get(street_name)
    if street_entry is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street_name, data["results"].keys()
        )

    location_id = street_entry.get(str(house_number_value))
    if location_id is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "house_number",
            house_number_value,
            street_entry.keys(),
        )
    return location_id


@final
class Source(BaseSource):
    TITLE = "Stadtreinigung Leipzig"
    DESCRIPTION = "Source for Stadtreinigung Leipzig."
    URL = "https://stadtreinigung-leipzig.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Bahnhofsallee": {"street": "Bahnhofsallee", "house_number": 7}
    }

    PARAMS = (street(), house_number())

    retrieve = LookupChainRetriever(
        steps=(_resolve_position,),
        url=_ICS_URL,
        params=lambda position_nos, street, house_number, **_: {
            "position_nos": position_nos,
            "name": f"{street} {house_number}",
            "mode": "download",
        },
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(clean=_clean, type_value_map=_TYPE_VALUE_MAP)
