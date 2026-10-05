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
    TITLE = "Lake Macquarie City Council"
    DESCRIPTION = "Source for Lake Macquarie City Council, Australia."
    URL = "https://www.lakemac.com.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "TestcaseII": {"address": "386 Pacific Highway, MURRAYS BEACH NSW 2281"}
    }

    PARAMS = (street_address(field="address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.lakemac.com.au",
        headers={
            "referer": "https://www.lakemac.com.au/For-residents/Waste-and-recycling/When-are-your-bins-collected"
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
