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
    TITLE = "Rural City of Wangaratta"
    DESCRIPTION = "Source for Rural City of Wangaratta rubbish collection."
    URL = "https://www.wangaratta.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Wangaratta High School": {
            "street_address": "Edwards Street WANGARATTA VIC 3677"
        },
        "KFC Wangaratta": {"street_address": "23-27 Ryley Street WANGARATTA VIC 3677"},
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GLASS,
    ]

    retrieve = OpenCitiesRetriever(
        domain="https://www.wangaratta.vic.gov.au",
        address="street_address",
        warm_up_url="https://www.wangaratta.vic.gov.au/Services/Waste-Recycling/Kerbside-Collection/Check-your-bin-day",
    )
    parse = OpenCitiesParser(exclude_type_prefixes=("Calendar",))
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            **TYPE_VALUE_MAP,
        },
    )
