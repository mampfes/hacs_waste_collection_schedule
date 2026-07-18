"""Kreisstadt Groß-Gerau waste calendar (Sitepark IES platform).

A declarative BaseSource pipeline. The shared ``SiteparkIESRetriever`` resolves
the street (and optional Ort) to a pois via a fixed district ``refid`` and
returns the raw ICS response; the shared ``IcsParser`` + ``ICSTransformer`` do
the parsing and typing. This module only declares the municipality's base URL,
refid and the German-to-canonical waste-type map, so there is no ``retrieve``
override, no manual request params and no ICON_MAP.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.service.SiteparkIES import SiteparkIESRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import PAPER, RECYCLABLES

_BASE_URL = "https://www.gross-gerau.de"


@final
class Source(BaseSource):
    TITLE = "Kreisstadt Groß-Gerau"
    DESCRIPTION = "Source for Kreisstadt Groß-Gerau waste collection."
    URL = _BASE_URL
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Adam-Rauch-Straße (Groß-Gerau)": {
            "strasse": "Adam-Rauch-Straße",
            "ort": "Groß-Gerau",
        },
    }

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(_BASE_URL, refid="3411.1")
    parse = parsers.IcsParser()
    # "Biotonne", "Papiertonne" and "Restmülltonne" already auto-resolve against
    # the shared vocabulary; the combined/size-suffixed labels below don't
    # match an alias exactly, so they need an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Gelbe Tonne - Gelber Sack": RECYCLABLES,
            "Papiertonne 1100 Liter": PAPER,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
