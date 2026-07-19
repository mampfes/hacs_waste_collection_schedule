"""Abfallwirtschaftsbetrieb Ilm-Kreis waste calendar (Sitepark IES platform).

A declarative BaseSource pipeline. The shared ``SiteparkIESRetriever`` resolves
the street (and optional Ort) to a pois and returns the raw ICS response; the
shared ``IcsParser`` + ``ICSTransformer`` do the parsing and typing. This
module only declares the municipality's base URL (a subdomain distinct from
the public ``URL``) and the German-to-canonical waste-type map, so there is no
``retrieve`` override, no manual request params and no ICON_MAP.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.service.SiteparkIES import SiteparkIESRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    ELECTRONICS,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://aik.ilm-kreis.de"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaftsbetrieb Ilm-Kreis"
    DESCRIPTION = "Source for Abfallwirtschaftsbetrieb Ilm-Kreis waste collection."
    URL = "https://www.ilm-kreis.de"
    COUNTRY = "de"

    WASTE_TYPES: ClassVar[list] = [
        ELECTRONICS,
        GENERAL_WASTE,
        HAZARDOUS,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Gerhart-Hauptmann-Straße (Arnstadt)": {
            "strasse": "Gerhart-Hauptmann-Straße",
            "ort": "Arnstadt",
        },
        "Ackermannstraße (Ilmenau)": {"strasse": "Ackermannstraße", "ort": "Ilmenau"},
    }

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(_BASE_URL)
    parse = parsers.IcsParser()
    # "Bioabfall", "Elektroschrott", "Restabfall" and "Sonderabfall" already
    # auto-resolve against the shared vocabulary; "Leichtverpackung" (singular)
    # and "Papier/Pappe" don't match an alias exactly, so they need an
    # explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Leichtverpackung": RECYCLABLES,
            "Papier/Pappe": PAPER,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
