from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import Deduplicate
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.JaduBinCollections import (
    tasks_parser,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "London Borough of Barnet"
    DESCRIPTION = "Source script for barnet.gov.uk"
    URL = "https://www.barnet.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "200062903"},
        "Test_002": {"uprn": "200072958"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://myforms.barnet.gov.uk/homepage/11/find-your-bin-collection-day",
        # The council's UPRNs are twelve digits, zero-padded.
        params=lambda uprn, **_: {"address": str(uprn).zfill(12)},
    )
    # The older bin-collection__ variant of the widget, dated "Wednesday, 30th
    # September".
    parse = tasks_parser(
        block="li.bin-collection",
        heading=".bin-collection__heading",
        date=".bin-collection__date",
        date_format="%A, %d %B",
    )
    preprocess = Deduplicate()
    transform = RowTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling Bin": wt.RECYCLABLES,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
