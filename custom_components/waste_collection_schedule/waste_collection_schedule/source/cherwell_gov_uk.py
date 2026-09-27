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
    TITLE = "Cherwell District Council"
    DESCRIPTION = "Cherwell District Council North Oxfordshire, UK"
    URL = "https://www.cherwell.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100120758315"},
        "Test_002": {"uprn": "100120780449"},
        "Test_003": {"uprn": 100120777153},
        "Test_004": {"uprn": 10011931488},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.cherwell.gov.uk/homepage/129/",
        # The council's UPRNs are twelve digits, zero-padded.
        params=lambda uprn, **_: {"uprn": str(uprn).zfill(12)},
    )
    parse = tasks_parser()
    transform = RowTransformer(
        clean=clean_heading,
        type_value_map={
            "Green Bin": wt.GENERAL_WASTE,
            "Blue Bin": wt.RECYCLABLES,
            "Brown Bin": wt.ORGANIC,
        },
    )
