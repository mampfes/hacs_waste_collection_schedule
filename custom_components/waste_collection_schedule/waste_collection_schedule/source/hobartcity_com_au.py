from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "City of Hobart"
    DESCRIPTION = "Source for City of Hobart"
    URL = "https://www.hobartcity.com.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "154 FOREST ROAD, WEST HOBART 7000": {
            "address": "154 FOREST ROAD, WEST HOBART 7000"
        },
        "151 AUGUSTA ROAD, LENAH VALLEY 7008": {
            "address": "151 AUGUSTA ROAD, LENAH VALLEY 7008"
        },
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "The address should exactly match the address autocompleted by the "
        "website: "
        "https://www.hobartcity.com.au/Residents/Waste-and-recycling/When-is-my-bin-collected"
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.hobartcity.com.au",
        page_link="/$720cfbd8-df7e-4b88-bf92-e218d51ee173$/Residents/Waste-and-recycling/When-is-my-bin-collected",
        strict_address_matching=True,
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={"FOGO/Green waste": wt.ORGANIC},
    )
