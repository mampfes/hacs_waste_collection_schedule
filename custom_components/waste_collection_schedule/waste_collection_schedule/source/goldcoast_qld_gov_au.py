from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    TYPE_VALUE_MAP,
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Gold Coast City Council"
    DESCRIPTION = "Source for Gold Coast Council rubbish collection."
    URL = "https://www.goldcoast.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "MovieWorx": {"street_address": "50 Millaroo Dr Helensvale"},
        "The Henchman": {"street_address": "6/8 Henchman Ave Miami"},
        "Pie Pie": {"street_address": "1887 Gold Coast Hwy Burleigh Heads"},
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.goldcoast.qld.gov.au",
        address="street_address",
        search_fuzzy=True,
        max_results=1,
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            **TYPE_VALUE_MAP,
        },
    )
