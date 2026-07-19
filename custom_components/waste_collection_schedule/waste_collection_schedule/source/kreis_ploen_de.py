"""Abfallwirtschaft Kreis Plön waste calendar (Sitepark IES platform).

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

_BASE_URL = "https://www.kreis-ploen.de"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Kreis Plön"
    DESCRIPTION = "Source for Abfallwirtschaft Kreis Plön waste collection."
    URL = _BASE_URL
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Hauptstraße (Köhn)": {"strasse": "Hauptstraße", "ort": "Köhn"},
        "Achterhof (Martensrade)": {"strasse": "Achterhof", "ort": "Martensrade"},
    }

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(_BASE_URL)
    parse = parsers.IcsParser()
    # "Gelber Sack" already auto-resolves against the shared vocabulary; every
    # other label carries a rhythm suffix (e.g. "2-wöchentlich") that doesn't
    # match an alias exactly, so each needs an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Bioabfall 2-wöchentlich": ORGANIC,
            "Papier 4-wöchentlich": PAPER,
            "Papiercontainer 4-wöchentlich": PAPER,
            "Restabfall 2-wöchentlich": GENERAL_WASTE,
            "Restabfall 4-wöchentlich": GENERAL_WASTE,
            "Restabfallcontainer 2-wöchentlich": GENERAL_WASTE,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
