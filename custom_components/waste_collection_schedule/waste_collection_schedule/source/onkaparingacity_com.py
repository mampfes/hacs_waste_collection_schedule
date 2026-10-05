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
    TITLE = "City of Onkaparinga Council"
    DESCRIPTION = "Source for City of Onkaparinga Council, Australia."
    URL = "https://www.onkaparingacity.com/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "TestcaseI": {"address": "18 Flagstaff Road, FLAGSTAFF HILL 5159"}
    }

    PARAMS = (street_address(field="address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.onkaparingacity.com",
        headers={
            "referer": "https://www.onkaparingacity.com/Services/Waste-and-recycling/Bin-collections"
        },
    )
    parse = OpenCitiesParser(exclude_type_prefixes=("Calendar",))
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            **TYPE_VALUE_MAP,
            "General waste (waste to landfill)": wt.GENERAL_WASTE,
        },
    )
