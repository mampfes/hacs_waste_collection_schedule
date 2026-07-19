"""Landkreis Peine waste calendar (Sitepark IES platform).

A declarative BaseSource pipeline. The shared ``SiteparkIESRetriever`` resolves
the street (and optional Ort) to a pois and returns the raw ICS response; the
shared ``IcsParser`` + ``ICSTransformer`` do the parsing and typing. This
module only declares the municipality's base URL and the German-to-canonical
waste-type map, so there is no ``retrieve`` override, no manual request params
and no ICON_MAP.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.service.SiteparkIES import SiteparkIESRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.ab-peine.de"


@final
class Source(BaseSource):
    TITLE = "Landkreis Peine"
    DESCRIPTION = (
        "Source for Abfallwirtschaftsbetrieb Landkreis Peine waste collection."
    )
    URL = "https://ab-peine.de"
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Gerhart-Hauptmann-Straße (Peine-Kernstadt)": {
            "strasse": "Gerhart-Hauptmann-Straße",
        },
        "Adlerstraße (Peine-Kernstadt)": {"strasse": "Adlerstraße"},
    }

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(_BASE_URL)
    parse = parsers.IcsParser()
    # "Altpapier", "Biotonne" and "Restmülltonne" already auto-resolve against
    # the shared vocabulary; only "Gelbe Säcke" (plural) needs an explicit map,
    # since the shared aliases only cover "gelber sack" (singular).
    transform = ICSTransformer(
        type_value_map={
            "Gelbe Säcke": RECYCLABLES,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
