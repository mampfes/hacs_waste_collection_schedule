from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode
from waste_collection_schedule.service.ThreeCWasteCalendar import (
    PARSE_DATE,
    TYPE_VALUE_MAP,
    CollectionsParser,
    address_retriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Deprecated in favour of greater_cambridge_waste_org, which UI configurations
# are migrated to automatically (init_ui.py). Kept working until it is removed.


@final
class Source(BaseSource):
    TITLE = "South Cambridgeshire District Council (Deprecated)"
    DESCRIPTION = (
        "Source for scambs.gov.uk services for South Cambridgeshire District Council"
    )
    URL = "https://scambs.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "houseNumber": {"post_code": "CB236GZ", "number": 53},
        "houseName": {"post_code": "CB225HT", "number": "Rectory Farm Cottage"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown postcode": {"post_code": "ZZ99ZZ", "number": 1},
    }

    PARAMS = (postcode("post_code"), house_number("number"))

    retrieve = address_retriever()
    parse = CollectionsParser()
    transform = RowTransformer(parse_date=PARSE_DATE, type_value_map=TYPE_VALUE_MAP)
