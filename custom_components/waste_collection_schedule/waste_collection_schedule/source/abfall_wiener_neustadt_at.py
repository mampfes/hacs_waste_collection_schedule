from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street, text_field
from waste_collection_schedule.service.WienerNeustadtCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Wiener Neustadt"
    DESCRIPTION = "Source for abfall.wiener-neustadt.at waste collection schedule for Wiener Neustadt, Austria"
    URL = "https://abfall.wiener-neustadt.at/"
    TEST_CASES: ClassVar[dict] = {
        "Martinsgasse Monthly": {"street": "Martinsgasse", "rm_art": "monatlich"},
        "Hauptplatz Weekly": {"street": "Hauptplatz", "rm_art": "wöchentlich"},
        "Leithakoloniestrasse Default": {"street": "Leithakoloniestraße"},
        "Leithakoloniestrasse Bi-Weekly": {
            "street": "Leithakoloniestraße",
            "rm_art": "14-tägig",
        },
    }
    HOWTO: ClassVar[dict] = {
        "en": "Visit the website https://abfall.wiener-neustadt.at/ and select your street from the dropdown menu. Note your street name and select the waste collection frequency that applies to your address.",
        "de": "Besuchen Sie die Website https://abfall.wiener-neustadt.at/ und wählen Sie Ihre Straße aus dem Dropdown-Menü. Notieren Sie sich Ihren Straßennamen und wählen Sie die Abfuhrhäufigkeit, die für Ihre Adresse gilt.",
    }
    COUNTRY = "at"
    PARAMS = (
        street(),
        text_field("str_id", "Street identifier", optional=True),
        text_field("rm_art", "Residual waste frequency", default="monatlich"),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Biotonne": wt.ORGANIC,
            "Wertstoffe": wt.RECYCLABLES,
            "Altkleider": wt.TEXTILES,
            "Christbaum": wt.GARDEN_WASTE,
        },
    )
