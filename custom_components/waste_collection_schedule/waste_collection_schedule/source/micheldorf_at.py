from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.micheldorf.at"


@final
class Source(BaseSource):
    TITLE = "Micheldorf in Oberösterreich"
    DESCRIPTION = "Source for Micheldorf in Oberösterreich, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

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
            "Restabfall 2-wöchentlich": wt.GENERAL_WASTE,
            "Restabfall 4-wöchentlich": wt.GENERAL_WASTE,
            "Restabfall 6-wöchentlich": wt.GENERAL_WASTE,
        },
    )
