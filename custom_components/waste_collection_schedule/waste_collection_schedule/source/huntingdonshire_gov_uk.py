from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.ThreeCWasteCalendar import (
    PARSE_DATE,
    TYPE_VALUE_MAP,
    CollectionsParser,
    uprn_retriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Huntingdonshire District Council"
    DESCRIPTION = "Source for Huntingdonshire.gov.uk services for Huntingdonshire District Council."
    URL = "https://www.huntingdonshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Wells Close, Brampton": {"uprn": "100090123510"},
        "Inkerman Rise, St. Neots": {"uprn": "10000144271"},
    }

    PARAMS = (uprn(),)

    retrieve = uprn_retriever(authority="HDC")
    parse = CollectionsParser()
    transform = RowTransformer(parse_date=PARSE_DATE, type_value_map=TYPE_VALUE_MAP)
