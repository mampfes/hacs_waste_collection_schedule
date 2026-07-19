from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
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

_BASE_URL = "https://www.schaerding.ooe.gv.at"


@final
class Source(BaseSource):
    TITLE = "Schärding"
    DESCRIPTION = "Source for Schärding, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Adalbert-Stifter-Straße 1": {
            "strasse": "Adalbert-Stifter-Straße",
            "hausnummer": "1",
        },
        "Aigerdinger Straße 2": {
            "strasse": "Aigerdinger Straße",
            "hausnummer": 2,
        },
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "226878372",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=(
            "https://www.schaerding.ooe.gv.at/system/web/kalender.aspx"
            "?menuonr=226878372"
        ),
    )
    parse = RiSKommunalParser()

    # "Restabfall N-wöchentlich" is cadence-suffixed and does not match the
    # shared vocabulary's plain "restabfall" alias verbatim. Restabfall,
    # Restmüll, Bioabfall, Biomüll, Altpapier, Papier, Gelber Sack, Gelbe
    # Tonne, Sperrmüll, Altglas and Problemstoff all resolve unmapped.
    transform = ICSTransformer(
        type_value_map={
            "Restabfall wöchentlich": GENERAL_WASTE,
            "Restabfall 2-wöchentlich": GENERAL_WASTE,
            "Restabfall 4-wöchentlich": GENERAL_WASTE,
            "Restabfall 6-wöchentlich": GENERAL_WASTE,
        },
    )

    def __init__(self, strasse: str, hausnummer: str | int):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
