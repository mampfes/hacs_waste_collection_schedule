from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Townsville"
    DESCRIPTION = "Source for Townsville."
    URL = "https://townsville.qld.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Woodwark Drive, Bushland Beach": {
            "property_id": "009fe2d01b9ba090598520202d4bcbc7"
        },
        "Riverway Dr, Kelso": {"property_id": "d41fe69c1b5ba090598520202d4bcb3c"},
        "37 Pilkington St, Garbutt": {
            "property_id": "580f6e5c1b5ba090598520202d4bcb91"
        },
    }

    PARAMS = (location_id("property_id"),)

    retrieve = HttpGetRetriever(
        url="https://mitownsville.service-now.com/api/cio19/bin_collection_dates/getBinCollectionCal",
        params=lambda property_id, **_: {"p_id": property_id},
        # A browser's Accept header makes the API answer XML.
        headers={"Accept": "application/json"},
    )
    parse = parsers.JsonParser("result")
    transform = JsonTransformer(
        date_key=lambda record: record["start"][:10],
        type_key="title",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={"Rubbish": wt.GENERAL_WASTE, "Recycle": wt.RECYCLABLES},
    )
