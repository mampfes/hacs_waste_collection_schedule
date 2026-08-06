from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.felixdorf.gv.at"
VALID_ZONES = ["Rayon 1", "Rayon 2"]


@final
class Source(BaseSource):
    TITLE = "Gemeinde Felixdorf"
    DESCRIPTION = "Source for Gemeinde Felixdorf, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
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
    # Felixdorf's third calendar column names the calendar a row belongs to,
    # and the municipality files its legal-advice slots there under
    # Kalendertyp="Rechtsberatung", beside Rayon 1 and Rayon 2. Leaving the
    # zone blank used to mean "keep every row", so the "all zones" setting
    # published four Rechtsberatung appointments as waste collections. Naming
    # the zones makes blank mean "both Rayons" instead.
    parse = RiSKommunalParser(zone_param="zone", zones=VALID_ZONES)

    # Restmüll/Papier are labelled with the container size (e.g. "Restmüll
    # 1.100-Liter-Container"), which does not match the shared vocabulary
    # verbatim. Windeltonne (nappy bin) has no canonical equivalent and is
    # mapped explicitly. Biotonne and Gelber Sack are classified by the shared
    # vocabulary.
    transform = ICSTransformer(
        type_value_map={
            "Restmüll 1.100-Liter-Container": wt.GENERAL_WASTE,
            "Restmüll 120 Liter und 240 Liter": wt.GENERAL_WASTE,
            "Papier 1.100-Liter-Container": wt.PAPER,
            "Papier 120 Liter und 240 Liter": wt.PAPER,
            "Windeltonne": wt.GENERAL_WASTE,
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
