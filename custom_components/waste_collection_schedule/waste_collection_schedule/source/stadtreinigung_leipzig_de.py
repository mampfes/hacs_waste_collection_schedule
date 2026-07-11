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

_STREETS_URL = "https://stadtreinigung-leipzig.de/rest/Navision/Streets"
_ICS_URL = (
    "https://stadtreinigung-leipzig.de/wir-kommen-zu-ihnen/abfallkalender/ical.ics"
)


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
    transform = ICSTransformer(clean=lambda s: s.removesuffix(", "))

    def __init__(self, street: str, house_number: int):
        super().__init__(street=street, house_number=house_number)
