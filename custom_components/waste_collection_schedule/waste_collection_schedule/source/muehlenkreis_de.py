"""Mühlenkreis Minden-Lübbecke waste calendar (Sitepark IES platform).

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
    BULKY_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.muehlenkreis.de"


@final
class Source(BaseSource):
    TITLE = "Mühlenkreis Minden-Lübbecke"
    DESCRIPTION = "Source for Mühlenkreis Minden-Lübbecke waste collection."
    URL = _BASE_URL
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Hauptstraße (Harlinghausen)": {
            "strasse": "Hauptstraße",
            "ort": "Harlinghausen",
        },
        "Berliner Straße (Bad Holzhausen)": {
            "strasse": "Berliner Straße",
            "ort": "Bad Holzhausen",
        },
    }

    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(_BASE_URL)
    parse = parsers.IcsParser()
    # "Elektroschrott" already auto-resolves against the shared vocabulary;
    # every other observed label either carries a rhythm suffix (e.g.
    # "4-wöchentlich") or is a compound that doesn't match an alias exactly,
    # so each needs an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Biotonne 2-wöchentlich": ORGANIC,
            "Gelbe Tonne 4-wöchentlich": RECYCLABLES,
            "Papiertonne 4-wöchentlich": PAPER,
            "Restmüll 4-wöchentlich": GENERAL_WASTE,
            "Schadstoffsammlung": HAZARDOUS,
            "Sperrmüllabfuhr": BULKY_WASTE,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
