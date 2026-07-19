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

_BASE_URL = "https://www.puchbeihallein.gv.at"


@final
class Source(BaseSource):
    TITLE = "Puch bei Hallein"
    DESCRIPTION = "Waste collection schedule for Puch bei Hallein, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@nerdoc"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Ahornstraße 3": {"strasse": "Ahornstraße", "hausnummer": "3"},
        "Austraße 2": {"strasse": "Austraße", "hausnummer": "2"},
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender, "
            "pick your street and house number from the dropdowns, and use the same values "
            "for 'strasse' and 'hausnummer'."
        ),
        "de": (
            "Öffnen Sie https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender, "
            "wählen Sie Ihre Straße und Hausnummer aus den Dropdown-Menüs, und verwenden Sie "
            "dieselben Werte für 'strasse' und 'hausnummer'."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "226095231",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=(
            "https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender"
        ),
        lookahead_days=365,
        max_pages=30,
    )
    parse = RiSKommunalParser(lookahead_days=365)

    # Restmüll, Biomüll, Altpapier and Gelber Sack all resolve via the shared
    # multilingual vocabulary; no explicit type_value_map entries are needed.
    transform = ICSTransformer()
