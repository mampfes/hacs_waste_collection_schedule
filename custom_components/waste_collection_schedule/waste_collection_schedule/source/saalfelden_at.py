from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

_BASE_URL = "https://www.saalfelden.at"


@final
class Source(BaseSource):
    TITLE = "Saalfelden am Steinernen Meer"
    DESCRIPTION = "Source for Saalfelden am Steinernen Meer waste collection."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Achenweg 1": {"strasse": "Achenweg", "hausnummer": 1},
        "Abdeckerweg 5": {"strasse": "Abdeckerweg", "hausnummer": "5"},
        "Achenweg 4a": {"strasse": "Achenweg", "hausnummer": "4a"},
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.saalfelden.at/Buergerservice/Abfallkalender, pick "
            "your street and house number from the dropdowns, and use the same "
            "values here."
        ),
        "de": (
            "Öffnen Sie https://www.saalfelden.at/Buergerservice/Abfallkalender, "
            "wählen Sie Ihre Straße und Hausnummer aus, und verwenden Sie dieselben "
            "Werte hier."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "detailonr": "225697049",
            "menuonr": "225696673",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url="https://www.saalfelden.at/Buergerservice/Abfallkalender",
        lookahead_days=365,
        max_pages=30,
    )
    parse = RiSKommunalParser(lookahead_days=365)

    # Restmüll, Biomüll, Gelbe Tonne, Gelber Sack, Altpapier/Papier, Sperrmüll
    # and Problemstoff all resolve via the shared multilingual vocabulary. Only
    # the singular Christbaum/Weihnachtsbaum (the seasonal tree-collection
    # round) need an explicit entry: the vocabulary's German aliases are
    # plural ("Christbäume"/"Weihnachtsbäume").
    transform = ICSTransformer(
        type_value_map={
            "Christbaum": GARDEN_WASTE,
            "Weihnachtsbaum": GARDEN_WASTE,
        },
    )
