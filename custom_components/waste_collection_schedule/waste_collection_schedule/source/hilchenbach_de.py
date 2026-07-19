"""Stadt Hilchenbach waste calendar (Sitepark IES platform).

A declarative BaseSource pipeline. The shared ``SiteparkIESRetriever`` resolves
the street (and optional Ortsteil) to a pois and returns the raw ICS response;
the shared ``IcsParser`` + ``ICSTransformer`` do the parsing and typing. This
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

_BASE_URL = "https://hilchenbach.de"


@final
class Source(BaseSource):
    TITLE = "Stadt Hilchenbach"
    DESCRIPTION = "Source for 'Abfallkalender Stadt Hilchenbach'."
    URL = "https://www.hilchenbach.de"
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
        "Dammstraße (Hilchenbach)": {"strasse": "Dammstr"},
        "Am Bühl (Allenbach)": {"strasse": "Am Bühl"},
    }

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Street name or a unique part of it. Optionally add the district "
            "(the part in parentheses, e.g. 'Allenbach') to disambiguate."
        ),
        "de": (
            "Straßenname oder eindeutiger Teil davon. Optional den Ortsteil "
            "(der Teil in Klammern, z.B. 'Allenbach') zur Eindeutigkeit angeben."
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(
        _BASE_URL,
        download_params={"kat": "1", "alarm": "0"},
    )
    parse = parsers.IcsParser()
    # "Biomüll", "Papier", "Restmüll", "Gelbe Tonne" and (if it occurs)
    # "Weihnachtsbäume" already auto-resolve against the shared vocabulary;
    # "Astschnitt" and "Schadstoffsammlung" don't match an alias exactly
    # (the shared aliases use "...schnitt"-compound / "schadstoff(e)" forms),
    # so they need an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Astschnitt": GARDEN_WASTE,
            "Schadstoffsammlung": HAZARDOUS,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
