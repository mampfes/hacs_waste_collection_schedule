"""Ostprignitz-Ruppin waste calendar (Sitepark IES platform).

A declarative BaseSource pipeline. The shared ``SiteparkIESRetriever`` resolves
the street (and optional Ort) to a pois and returns the raw ICS response; the
shared ``IcsParser`` + ``ICSTransformer`` do the parsing and typing. This
module only declares the municipality's base URL, download params and the
German-to-canonical waste-type map, so there is no ``retrieve`` override, no
manual request params and no ICON_MAP.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.service.SiteparkIES import SiteparkIESRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.ostprignitz-ruppin.de"


@final
class Source(BaseSource):
    TITLE = "Ostprignitz-Ruppin"
    DESCRIPTION = "Source for Ostprignitz-Ruppin waste collection."
    URL = _BASE_URL
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [
        GARDEN_WASTE,
        GENERAL_WASTE,
        HAZARDOUS,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Am alten Gymnasium (Neuruppin)": {
            "ort": "Neuruppin",
            "strasse": "Am alten Gymnasium",
        },
    }

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street. If the street name exists in several places, "
            "add the place name to disambiguate."
        ),
        "de": (
            "Geben Sie Ihre Straße ein. Kommt der Straßenname in mehreren "
            "Orten vor, geben Sie zusätzlich den Ort zur Eindeutigkeit an."
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(
        _BASE_URL,
        download_params={"monat": "", "alarm": "0"},
    )
    parse = parsers.IcsParser()
    # "Restmülltonne", "Biotonne", "Gelbe Tonne", "Blaue Tonne" and
    # "Schadstoffmobil" already auto-resolve against the shared vocabulary;
    # only "Grünabfallsammlung" doesn't match an alias exactly (the shared
    # aliases use the bare "grünabfall" form), so it needs an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Grünabfallsammlung": GARDEN_WASTE,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
