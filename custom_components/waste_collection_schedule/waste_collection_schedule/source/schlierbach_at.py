from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

_BASE_URL = "https://www.schlierbach.at"
VALID_ZONES = ["1", "Wohnhausanlagen"]


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Schlierbach"
    DESCRIPTION = "Source for Marktgemeinde Schlierbach waste collection."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]

    TEST_CASES: ClassVar[dict] = {
        "Gemeinde Alle (no zone)": {},
        "Zone 1": {"zone": "1"},
        "Wohnhausanlagen": {"zone": "Wohnhausanlagen"},
    }

    PARAMS = (dropdown("zone", VALID_ZONES, optional=True),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "The zone argument is optional. Zone '1' adds the 4-weekly "
            "Restabfall schedule; zone 'Wohnhausanlagen' adds the Gelbe Tonne "
            "schedule for residential complexes. Leave it out to receive all "
            "events regardless of zone."
        ),
        "de": (
            "Das Argument 'zone' ist optional. Zone '1' ergänzt den "
            "4-wöchentlichen Restabfall-Abholplan; Zone 'Wohnhausanlagen' "
            "ergänzt den Gelbe-Tonne-Plan für Wohnhausanlagen. Ohne Angabe "
            "werden alle Termine angezeigt."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "225603725",
        },
    )
    parse = RiSKommunalParser(zone_param="zone")

    # "Restabfall N-wöchentlich" is cadence-suffixed and does not match the
    # shared vocabulary's plain "restabfall" alias verbatim; Gelber Sack and
    # Gelbe Tonne resolve unmapped.
    transform = ICSTransformer(
        type_value_map={
            "Restabfall 2-wöchentlich": GENERAL_WASTE,
            "Restabfall 4-wöchentlich": GENERAL_WASTE,
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
