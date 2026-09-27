from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Mosman Council"
    DESCRIPTION = "Source for Mosman Council, NSW, Australia"
    URL = "https://mosman.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.ELECTRONICS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"address": "12 Shadforth Street"},
        "Test_002": {"address": "19 Rangers Avenue"},
        "Test_003": {"address": "14 Balmoral Avenue"},
    }

    PARAMS = (street_address(),)

    retrieve = HttpPostRetriever(
        url="https://apps.mosman.nsw.gov.au/test",
        data=lambda address, **_: {"address": address},
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key=lambda record: record["calendarDate"][:10],
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "generalWaste": wt.GENERAL_WASTE,
            "containersGlass": wt.RECYCLABLES,
            "paperCardboard": wt.PAPER,
            "vegetation": wt.GARDEN_WASTE,
            "generalCleanUp": wt.BULKY_WASTE,
            "ewaste": wt.ELECTRONICS,
        },
    )
