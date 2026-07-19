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

_BASE_URL = "https://www.eggelsberg.at"
VALID_ZONES = ["A", "B"]


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Eggelsberg"
    DESCRIPTION = "Source for Marktgemeinde Eggelsberg waste collection."
    URL = _BASE_URL
    COUNTRY = "at"

    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Zone A": {"zone": "A"},
        "Zone B": {"zone": "B"},
    }

    PARAMS = (dropdown("zone", VALID_ZONES),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your zone (A or B). This determines your Bioabfall "
            "(organic waste) collection schedule. All other waste types "
            "apply to all zones."
        ),
        "de": (
            "Wählen Sie Ihre Zone (A oder B). Dies bestimmt Ihren "
            "Bioabfall-Abholplan. Alle anderen Abfallarten gelten für alle "
            "Zonen."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "blnr": "",
            "gnr_search": "0",
            "menuonr": "224085238",
            "umkreis": "",
            "useronr": "0",
        },
        vdatum_today=True,
    )
    parse = RiSKommunalParser(zone_param="zone")

    # "Restabfall N-wöchentlich" is cadence-suffixed and does not match the
    # shared vocabulary's plain "restabfall" alias verbatim; Bioabfall,
    # Altpapier and Gelber Sack resolve unmapped.
    transform = ICSTransformer(
        type_value_map={
            "Restabfall 2-wöchentlich": GENERAL_WASTE,
            "Restabfall 4-wöchentlich": GENERAL_WASTE,
            "Restabfall 6-wöchentlich": GENERAL_WASTE,
        },
    )

    def __init__(self, zone: str):
        zone = zone.strip().upper()
        if zone not in VALID_ZONES:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone", zone, suggestions=VALID_ZONES
            )
        super().__init__(zone=zone)
