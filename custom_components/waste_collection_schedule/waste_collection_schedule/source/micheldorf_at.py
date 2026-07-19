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

_BASE_URL = "https://www.micheldorf.at"


@final
class Source(BaseSource):
    TITLE = "Micheldorf in Oberösterreich"
    DESCRIPTION = "Source for Micheldorf in Oberösterreich, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Adalbert-Stifter-Straße 1": {
            "strasse": "Adalbert-Stifter-Straße",
            "hausnummer": "1",
        },
        "Alterpichlstraße 2": {
            "strasse": "Alterpichlstraße",
            "hausnummer": "2",
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
            "menuonr": "227975509",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=(
            "https://www.micheldorf.at/system/web/kalender.aspx"
            "?sprache=1&menuonr=227975509"
        ),
    )
    parse = RiSKommunalParser()

    # "Restabfall N-wöchentlich" is cadence-suffixed and does not match the
    # shared vocabulary's plain "restabfall" alias verbatim; Bioabfall,
    # Altpapier, Gelber Sack, Sperrmüll and Altglas all resolve unmapped.
    transform = ICSTransformer(
        type_value_map={
            "Restabfall 2-wöchentlich": GENERAL_WASTE,
            "Restabfall 4-wöchentlich": GENERAL_WASTE,
            "Restabfall 6-wöchentlich": GENERAL_WASTE,
        },
    )

    def __init__(self, strasse: str, hausnummer: str):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
