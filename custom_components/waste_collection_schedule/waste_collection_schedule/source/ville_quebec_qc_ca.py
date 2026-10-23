from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.parsers import HtmlCalendarGrid
from waste_collection_schedule.service.QuebecCityCalendar import (
    CalendarRetriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Québec (QC)"
    DESCRIPTION = "Source script for Québec city waste collection"
    URL = "https://www.ville.quebec.qc.ca/services/info-collecte/"
    TEST_CASES: ClassVar[dict] = {
        "multiple results with unique id": {
            "street_number_and_name": "430 4e rue",
            "unique_id": "219232-134009",
        }
    }
    HOWTO: ClassVar[dict] = {
        "en": "You need to provide your street number and name in Quebec City.",
        "fr": "Vous devez fournir votre numéro et nom de rue dans la ville de Québec.",
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "no_published_schedule": {
            "street_number_and_name": "1935, Boulevard Henri-Bourassa"
        }
    }
    COUNTRY = "ca"
    PARAMS = (
        street_address("street_number_and_name"),
        text_field("unique_id", "Address identifier", optional=True),
    )

    retrieve = CalendarRetriever()
    parse = HtmlCalendarGrid(
        table="table.calendrier",
        header="caption",
        marker="p.img img",
        attribute=("title", "alt"),
    )
    transform = RowTransformer(
        type_value_map={
            "Ordures et résidus alimentaires": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
            "Recyclage": wt.RECYCLABLES,
            "Feuilles": wt.GARDEN_WASTE,
            "Garbage": wt.GENERAL_WASTE,
            "Garbage and Food Waste": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
            "Recycling": wt.RECYCLABLES,
            "Organic Waste": wt.ORGANIC,
            "Yard Waste": wt.GARDEN_WASTE,
            "Bulky Waste": wt.BULKY_WASTE,
            "Christmas Trees": wt.GARDEN_WASTE,
        },
    )
