from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.EdpFutureWeb import (
    TYPE_VALUE_MAP,
    EdpFutureWebParser,
    EdpFutureWebRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://future.molndal.se/FutureWeb/SimpleWastePickup"


@final
class Source(BaseSource):
    TITLE = "Mölndal"
    DESCRIPTION = "Source for Mölndal waste collection."
    URL = "https://molndal.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "105000": {"facility_id": "105000"},
        "109400": {"facility_id": 109400},
    }

    PARAMS = (text_field("facility_id", "Facility ID"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search your address at https://future.molndal.se/FutureWeb/"
            "SimpleWastePickup and use the number in brackets as 'facility_id'."
        ),
    }

    retrieve = EdpFutureWebRetriever(_API_URL, address=None, building_id="facility_id")
    parse = EdpFutureWebParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        carry_raw_label=True,
    )
