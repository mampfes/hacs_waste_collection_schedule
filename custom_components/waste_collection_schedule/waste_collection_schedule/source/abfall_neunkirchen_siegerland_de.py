"""Neunkirchen Siegerland waste calendar (Sitepark IES platform).

A declarative BaseSource pipeline. The shared ``SiteparkIESRetriever`` resolves
the street (and optional Ortsteil) to a pois and returns the raw ICS response;
the shared ``IcsParser`` + ``ICSTransformer`` do the parsing and typing. This
module only declares the municipality's base URL, refid and download params plus
the German-to-canonical waste-type map, so there is no ``retrieve`` override, no
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

_BASE_URL = "https://www.neunkirchen-siegerland.de"


@final
class Source(BaseSource):
    TITLE = "Neunkirchen Siegerland"
    DESCRIPTION = "Source for 'Abfallkalender Neunkirchen Siegerland'."
    URL = _BASE_URL
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]

    TEST_CASES: ClassVar[dict] = {
        "Waldstraße": {"strasse": "Waldstr"},
        "Altenseelbacher Weg (Neunkirchen)": {
            "strasse": "Altenseelbacher Weg",
            "ort": "Neunkirchen",
        },
    }

    PARAMS = (
        street("strasse"),
        district("ort", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter a partial or full street name as shown on the Neunkirchen "
            "Siegerland waste calendar (e.g. 'Waldstr' for 'Waldstraße'). If the "
            "street exists in several districts, add the district (Ortsteil) "
            "shown in parentheses (e.g. 'Neunkirchen')."
        ),
        "de": (
            "Geben Sie einen Teil oder den vollständigen Straßennamen wie im "
            "Abfallkalender Neunkirchen Siegerland ein (z.B. 'Waldstr' für "
            "'Waldstraße'). Kommt die Straße in mehreren Ortsteilen vor, "
            "ergänzen Sie den Ortsteil in Klammern (z.B. 'Neunkirchen')."
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(
        _BASE_URL,
        refid="3362.1",
        download_params={"kat": "1", "alarm": "0"},
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Biotonne": ORGANIC,
            "Papiertonne / Papiercontainer": PAPER,
            "Restmülltonne": GENERAL_WASTE,
            "Spartonne Restmüll": GENERAL_WASTE,
            "Container Restmüll": GENERAL_WASTE,
            "Gelbe Tonne": RECYCLABLES,
            "Astschnittsammlung": GARDEN_WASTE,
            "Schadstoffsammlung": HAZARDOUS,
        }
    )

    def __init__(self, strasse: str, ort: str | None = None):
        super().__init__(strasse=strasse, ort=ort)
