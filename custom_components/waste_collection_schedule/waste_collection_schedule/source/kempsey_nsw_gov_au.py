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
    TITLE = "Kempsey Shire Council"
    DESCRIPTION = "Source script for kempsey.nsw.gov.au waste collection services."
    URL = "https://www.kempsey.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GARDEN_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "10-12 Smith Street Kempsey": {"address": "10-12 Smith Street Kempsey"},
        "1 Belgrave Street Kempsey": {"address": "1 Belgrave Street Kempsey"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "99 Nowhere Street Kempsey"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address as it appears on the Kempsey Shire "
            "Council website, e.g. '10-12 Smith Street Kempsey'."
        ),
    }

    retrieve = OpenCitiesRetriever(
        "https://www.kempsey.nsw.gov.au",
        page_link=(
            "/$b9015858-988c-48a4-9473-7c193df083e4$"
            "/Residents/Waste-recycling/Waste-bin-collection"
        ),
    )
    parse = OpenCitiesParser()
    # The council publishes only the next date per bin; its note states the
    # cadence (green weekly, recycling and general waste fortnightly).
    preprocess = OpenCitiesProjection(weeks=26)
    transform = JsonTransformer(
        date_key="date", type_key="type", type_value_map=TYPE_VALUE_MAP
    )
