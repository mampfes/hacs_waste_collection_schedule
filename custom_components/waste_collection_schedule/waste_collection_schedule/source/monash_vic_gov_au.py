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
    TITLE = "City of Monash"
    DESCRIPTION = "Source for City of Monash rubbish collection."
    URL = "https://www.monash.vic.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"address": "4 Carson Street, Mulgrave 3170"},
        "Test_002": {"address": "57 Hamilton Place, Mount Waverley 3149"},
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Visit the [City of "
        "Monash](https://www.monash.vic.gov.au/Waste-Sustainability/Bin-Collection/When-we-collect-your-bins) "
        '"When we collect your bins" page and search for your address. For '
        "example: 4 Carson Street, Mulgrave 3170. The arguments should exactly "
        "match the full street address after selecting the autocomplete result."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.monash.vic.gov.au",
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
