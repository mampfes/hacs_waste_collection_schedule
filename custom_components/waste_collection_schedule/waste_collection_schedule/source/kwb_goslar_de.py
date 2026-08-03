"""Kreiswirtschaftsbetriebe Goslar waste calendar (Sitepark IES platform).

The shared ``SiteparkIESRetriever`` resolves the street/Ort to a pois and
returns the raw ICS response; the shared ``IcsParser`` + ``ICSTransformer`` do
the parsing and typing. This provider also accepts a direct ``pois`` id (e.g.
printed on a household's collection card), which the retriever's ``pois``
option takes straight to the download, so the source is a plain composition of
shared steps.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    district,
    street,
    text_field,
)
from waste_collection_schedule.service.SiteparkIES import SiteparkIESRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    ELECTRONICS,
    GARDEN_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.kwb-goslar.de"


@final
class Source(BaseSource):
    TITLE = "Kreiswirtschaftsbetriebe Goslar"
    DESCRIPTION = "Source for kwb-goslar.de waste collection."
    URL = _BASE_URL
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [
        ELECTRONICS,
        GARDEN_WASTE,
        GENERAL_WASTE,
        HAZARDOUS,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Berliner Straße (Clausthal-Zellerfeld)": {"pois": "2523.602"},
        "Braunschweiger Straße (Seesen)": {"pois": "2523.409"},
        "Marktstraße (Seesen)": {"strasse": "Marktstraße", "ort": "Seesen"},
    }

    PARAMS = (
        alternatives(
            [street("strasse")],
            [text_field("pois", label="POIS")],
        ),
        district("ort", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street (optionally with the place to disambiguate), "
            "or a direct POIS id if you already have one."
        ),
        "de": (
            "Geben Sie Ihre Straße ein (optional mit Ort zur Eindeutigkeit), "
            "oder eine direkte POIS-ID, falls bereits bekannt."
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(_BASE_URL, pois="pois")
    parse = parsers.IcsParser()
    # "Baum- und Strauchschnitt", "Biotonne", "Blaue Tonne", "Gelbe Tonne" and
    # "Restmülltonne" already auto-resolve against the shared vocabulary;
    # "Mobile Elektroaltgerätesammlung" and "Mobile Schadstoffsammlung" don't
    # match an alias exactly (the shared aliases don't carry the "Mobile ...
    # -sammlung" wording), so each needs an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Mobile Elektroaltgerätesammlung": ELECTRONICS,
            "Mobile Schadstoffsammlung": HAZARDOUS,
        }
    )
