from typing import ClassVar, final

from waste_collection_schedule import field_terms
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.service.AppAbfallplusDe import (
    AppAbfallplusParser,
    AppAbfallplusRetriever,
    discover_choices,
)
from waste_collection_schedule.transformers import JsonTransformer

APP_ID = "de.abfallplus.ahe"


@final
class Source(BaseSource):
    TITLE = "AHE Ennepe-Ruhr-Kreis"
    DESCRIPTION = "Source for AHE Ennepe-Ruhr-Kreis."
    URL = "https://ahe.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Wetter Ahornstraße alle Hausnummern": {
            "city": "Wetter",
            "strasse": "Ahornstraße",
            "hnr": "Alle Hausnummern",
        },
        "Herdecke Alte Straße 1": {
            "city": "Herdecke",
            "strasse": "Alte Straße",
            "hnr": "1",
        },
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Visit [https://ahe.de/abfallkalender/](https://ahe.de/abfallkalender/) and select your city and street. Use the exact city name as the `city` parameter (e.g. `Wetter`, `Herdecke`, `Gevelsberg`)."
    }

    PARAMS = (
        cascading_select(
            ("city", field_terms.MUNICIPALITY),
            ("bezirk", field_terms.DISTRICT),
            ("strasse", field_terms.STREET),
            ("hnr", field_terms.HOUSE_NUMBER),
        ),
    )

    retrieve = AppAbfallplusRetriever(app_id=APP_ID)
    parse = AppAbfallplusParser()
    transform = JsonTransformer(date_key="date", type_key="category")

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        return discover_choices(APP_ID, field, selections)
