from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.felixdorf.gv.at"
VALID_ZONES = ["Rayon 1", "Rayon 2"]


@final
class Source(BaseSource):
    TITLE = "Gemeinde Felixdorf"
    DESCRIPTION = "Source for Gemeinde Felixdorf, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]

    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rayon 1": {"zone": "Rayon 1"},
        "Rayon 2": {"zone": "Rayon 2"},
        "All zones": {},
    }

    PARAMS = (dropdown("zone", VALID_ZONES, optional=True),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your collection zone (Rayon 1 or Rayon 2). Leave blank to "
            "receive all zones."
        ),
        "de": (
            "Wählen Sie Ihre Abholzone (Rayon 1 oder Rayon 2). Leer lassen für "
            "alle Zonen."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "blnr": "",
            "gnr_search": "0",
            "menuonr": "219384069",
        },
    )
    parse = RiSKommunalParser(zone_param="zone")

    # Restmüll/Papier are labelled with the container size (e.g. "Restmüll
    # 1.100-Liter-Container"), which does not match the shared vocabulary
    # verbatim. Windeltonne (nappy bin) has no canonical equivalent and is
    # mapped explicitly. "Rechtsberatung" (a legal-advice slot, not a waste
    # collection) legitimately has none and is preserved verbatim, matching
    # the legacy behaviour of an unmapped label with no icon. Biotonne and
    # Gelber Sack are classified by the shared vocabulary.
    transform = ICSTransformer(
        type_value_map={
            "Restmüll 1.100-Liter-Container": GENERAL_WASTE,
            "Restmüll 120 Liter und 240 Liter": GENERAL_WASTE,
            "Papier 1.100-Liter-Container": PAPER,
            "Papier 120 Liter und 240 Liter": PAPER,
            "Windeltonne": GENERAL_WASTE,
        },
    )

    def __init__(self, zone: str | None = None):
        if zone is not None:
            zone = zone.strip()
            if zone not in VALID_ZONES:
                raise SourceArgumentNotFoundWithSuggestions(
                    "zone", zone, suggestions=VALID_ZONES
                )
        super().__init__(zone=zone)
