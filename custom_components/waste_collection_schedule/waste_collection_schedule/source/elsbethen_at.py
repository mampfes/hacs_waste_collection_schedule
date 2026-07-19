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

_BASE_URL = "https://www.gde-elsbethen.at"


@final
class Source(BaseSource):
    TITLE = "Elsbethen"
    DESCRIPTION = "Source for Elsbethen waste collection."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Überfuhrstraße 2": {"strasse": "Überfuhrstraße", "hausnummer": "2"},
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.gde-elsbethen.at/Buergerservice/Abfall-Recycling/Abfallkalender, "
            "pick your street and house number from the dropdowns, and use the same values here."
        ),
        "de": (
            "Öffnen Sie https://www.gde-elsbethen.at/Buergerservice/Abfall-Recycling/Abfallkalender, "
            "wählen Sie Ihre Straße und Hausnummer aus, und verwenden Sie dieselben Werte hier."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "menuonr": "225141707",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=(
            "https://www.gde-elsbethen.at/system/web/kalender.aspx?menuonr=223627736"
        ),
        lookahead_days=365,
        max_pages=30,
    )
    parse = RiSKommunalParser(lookahead_days=365)

    # Restmüll, Biomüll, Gelber Sack and Altpapier all resolve via the shared
    # multilingual vocabulary; no explicit type_value_map entries are needed.
    transform = ICSTransformer()
