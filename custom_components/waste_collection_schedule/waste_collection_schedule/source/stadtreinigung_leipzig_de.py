"""Stadtreinigung Leipzig.

Demonstrates: a two-step address lookup (street/house-number search resolves
an opaque position id) feeding a single ICS download — no year window or
feed fan-out here, but the lookup itself must run inside a custom
``retrieve`` since the second request depends on the first response.
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

    def retrieve(self, source):
        params = {"old_format": 1, "search": self.params["street"]}
        r = self.session.get(_STREETS_URL, params=params)

        data = json.loads(r.text)
        if len(data["results"]) == 0:
            raise SourceArgumentNotFound("street", self.params["street"])
        street_entry = data["results"].get(self.params["street"])
        if street_entry is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self.params["street"], data["results"].keys()
            )

        location_id = street_entry.get(str(self.params["house_number"]))
        if location_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number",
                self.params["house_number"],
                street_entry.keys(),
            )

        ics_params = {
            "position_nos": location_id,
            "name": f"{self.params['street']} {self.params['house_number']}",
            "mode": "download",
        }
        return self.session.get(_ICS_URL, params=ics_params)

    parse = parsers.IcsParser()
    transform = ICSTransformer(clean=_clean, type_value_map=_TYPE_VALUE_MAP)

    def __init__(self, street: str, house_number: int):
        super().__init__(street=street, house_number=house_number)
