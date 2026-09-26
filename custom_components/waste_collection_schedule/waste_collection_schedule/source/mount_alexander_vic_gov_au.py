from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    TYPE_VALUE_MAP,
    OpenCitiesParser,
    OpenCitiesProjection,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Mount Alexander Shire Council"
    DESCRIPTION = "Source for Mount Alexander Shire Council, VIC, Australia."
    URL = "https://www.mountalexander.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Campbells Creek": {"address": "123 Main Road Campbells Creek Victoria 3451"},
        "Castlemaine": {"address": "1 Mostyn Street Castlemaine Victoria 3450"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "99 Nowhere Street Castlemaine Victoria 3450"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address as it appears on the council "
            "website, e.g. '1 Mostyn Street Castlemaine Victoria 3450'."
        ),
    }

    retrieve = OpenCitiesRetriever(
        "https://www.mountalexander.vic.gov.au",
        page_link="/My-Property/Waste-and-recycling/Find-your-bin-collection-day",
    )
    parse = OpenCitiesParser()
    # The council publishes only the next date per bin; its note states the
    # cadence (weekly or fortnightly).
    preprocess = OpenCitiesProjection(weeks=26)
    transform = JsonTransformer(
        date_key="date", type_key="type", type_value_map=TYPE_VALUE_MAP
    )
