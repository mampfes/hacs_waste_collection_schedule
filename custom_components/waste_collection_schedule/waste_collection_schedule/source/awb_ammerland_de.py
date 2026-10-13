from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, city, street, text_field
from waste_collection_schedule.service.AmmerlandApp import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "AWB Ammerland"
    DESCRIPTION = (
        "Source for AWB Ammerland (Abfallwirtschaftsbetrieb Landkreis Ammerland)."
    )
    URL = "https://www.awb-ammerland.de"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Edewecht - Schepser Damm": {"city": "Edewecht", "street": "Schepser Damm"},
        "Westerstede - Ammerlandallee nördlich A28": {
            "city": "Westerstede",
            "street": "Ammerlandallee",
            "street_section": "nördl.d. A 28",
        },
        "Wiefelstede - Ahlerskamp (4-wöchentl. Restabfall)": {
            "city": "Wiefelstede",
            "street": "Ahlerskamp",
            "four_weekly_rest": True,
        },
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "de": "Nur erforderlich, wenn die Straße in mehrere Abschnitte aufgeteilt ist (z.B. 'nördl.d. A 28'). Aktivieren, wenn ein 4-wöchentlicher Abfuhrrythmus für die Restabfalltonne beantragt wurde.",
        "en": "Only required if the street is divided into sections (e.g. 'nördl.d. A 28'). Enable if a 4-weekly collection interval for residual waste has been requested.",
    }
    PARAMS = (
        city(),
        street(),
        text_field("street_section", "Street section", optional=True),
        boolean(
            "four_weekly_rest", "4-weekly residual waste collection", default=False
        ),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Restabfall": wt.GENERAL_WASTE,
            "Bioabfall": wt.ORGANIC,
            "Gelber Sack": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Ast- und Strauchwerk": wt.GARDEN_WASTE,
            "Problemstoffe": wt.HAZARDOUS,
        },
    )
