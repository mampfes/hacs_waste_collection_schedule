from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.BinsPropertyPortal import next_service_parser
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Bridgend County Borough Council"
    DESCRIPTION = "Source for bridgend.gov.uk"
    URL = "https://www.bridgend.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "test_001": {"uprn": "100100479873"},
        "test_002": {"uprn": 10032996088},
        "test_003": {"uprn": "10090813443"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: (
            f"https://bridgendportal.azurewebsites.net/property/{uprn}"
        ),
    )
    parse = next_service_parser()
    transform = RowTransformer(
        type_value_map={
            "Recycling collection": wt.RECYCLABLES,
            "Refuse collection": wt.GENERAL_WASTE,
            "Refuse Sacks collection": wt.GENERAL_WASTE,
            "Garden Waste collection": wt.GARDEN_WASTE,
        },
    )
