"""Landkreis Mecklenburgische Seenplatte waste calendar (Sitepark IES platform).

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
from waste_collection_schedule.waste_types import GENERAL_WASTE

_BASE_URL = "https://www.lk-mecklenburgische-seenplatte.de"


@final
class Source(BaseSource):
    TITLE = "Landkreis Mecklenburgische Seenplatte"
    DESCRIPTION = "Source for Landkreis Mecklenburgische Seenplatte waste collection."
    URL = _BASE_URL
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Atelierstraße (Neubrandenburg)": {
            "ort": "Neubrandenburg",
            "strasse": "Atelierstraße",
        },
        "Dargun": {"ort": "Dargun", "strasse": "Dargun"},
    }

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(_BASE_URL)
    parse = parsers.IcsParser()
    # "Biotonne", "Gelbe Tonne" and "Papiertonne" already auto-resolve against
    # the shared vocabulary; "Restmülltonne" carries a rhythm suffix (e.g.
    # "14-täglichen Rhythmus") that doesn't match the alias exactly, so each
    # observed variant needs an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Restmülltonne 14-täglichen Rhythmus": GENERAL_WASTE,
            "Restmülltonne 28-täglichen Rhythmus": GENERAL_WASTE,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
