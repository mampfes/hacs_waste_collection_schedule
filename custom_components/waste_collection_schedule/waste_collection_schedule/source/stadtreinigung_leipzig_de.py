"""Stadtreinigung Leipzig.

A two-step address lookup (a street/house-number search resolves an opaque
position id) feeding a single ICS download, which is the shared
``LookupChainRetriever``: a declared ``Lookup`` resolves the id and the
retriever fetches the calendar with it.
"""

import json
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_STREETS_URL = "https://stadtreinigung-leipzig.de/rest/odata/Streets"
_ICS_URL = (
    "https://stadtreinigung-leipzig.de/wir-kommen-zu-ihnen/abfallkalender/ical.ics"
)

# The feed labels bins "<bin> (Abholzeit)" (and sometimes a trailing ", "), which
# the shared vocabulary does not match. Drop the parenthetical and reduce the
# label to its core bin term for the type_value_map.
_TYPE_VALUE_MAP = {
    "biotonne": wt.ORGANIC,
    "gelbe tonne": wt.RECYCLABLES,
    "blaue tonne": wt.PAPER,
    "restabfall": wt.GENERAL_WASTE,
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


def _pick_position(response, street: str, house_number, **_) -> str:
    """The feed's opaque position ids for the street and house number.

    A house number can have several positions (e.g. one per bin), and the
    calendar takes them all comma-separated.
    """
    streets = json.loads(response.text).get("results") or []
    if len(streets) == 0:
        raise SourceArgumentNotFound("street", street)
    numbers = [
        number
        for entry in streets
        if entry.get("name") == street
        for number in entry.get("numbers") or []
    ]
    if not numbers:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street, sorted({s.get("name") for s in streets})
        )

    position_nos = [
        position
        for number in numbers
        if str(number.get("number")) == str(house_number)
        for position in number.get("position_nos") or []
    ]
    if not position_nos:
        raise SourceArgumentNotFoundWithSuggestions(
            "house_number",
            house_number,
            [n.get("number") for n in numbers],
        )
    return ",".join(position_nos)


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
        steps=(
            Lookup(
                _STREETS_URL,
                params=lambda street, **_: {"search": street},
                pick=_pick_position,
                raise_for_status=True,
            ),
        ),
        url=_ICS_URL,
        params=lambda position_nos, street, house_number, **_: {
            "position_nos": position_nos,
            "name": f"{street} {house_number}",
            "mode": "download",
        },
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(clean=_clean, type_value_map=_TYPE_VALUE_MAP)
