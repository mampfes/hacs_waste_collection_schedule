from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.BinsPropertyPortal import next_service_parser
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Shropshire Council"
    DESCRIPTION = "Source for Shropshire Council."
    URL = "https://shropshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "100070056686": {"uprn": 100070056686},
        "200000119191": {"uprn": "200000119191"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: f"https://bins.shropshire.gov.uk/property/{uprn}",
    )
    parse = next_service_parser()
    transform = RowTransformer(
        type_value_map={
            "General Waste Collection": wt.GENERAL_WASTE,
            "Recycling Collection": wt.RECYCLABLES,
            "Garden Waste Collection": wt.GARDEN_WASTE,
        },
    )
