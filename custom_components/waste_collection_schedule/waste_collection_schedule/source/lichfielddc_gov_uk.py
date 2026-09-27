from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.JaduBinCollections import (
    clean_heading,
    tasks_parser,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Lichfield District Council"
    DESCRIPTION = "Source for Lichfield District Council, UK."
    URL = "https://lichfielddc.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100031695248"},
        "Test_002": {"uprn": "100031704571"},
        "Test_003": {"uprn": "10002768095"},
        "Test_004": {"uprn": "100031699855"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.lichfielddc.gov.uk/bincalendar",
        # The council's UPRNs are twelve digits, zero-padded.
        params=lambda uprn, **_: {"uprn": str(uprn).zfill(12)},
    )
    parse = tasks_parser()
    transform = RowTransformer(
        clean=clean_heading,
        type_value_map={
            "Black Bin": wt.GENERAL_WASTE,
            "Black Bag": wt.GENERAL_WASTE,
            "Blue Bin": wt.RECYCLABLES,
            "Blue Bag": wt.RECYCLABLES,
            "Brown Bin": wt.GARDEN_WASTE,
            "Food Caddy": wt.FOOD_WASTE,
            "Purple Bin": wt.RECYCLABLES,
        },
    )
