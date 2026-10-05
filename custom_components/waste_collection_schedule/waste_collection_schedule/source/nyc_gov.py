from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    DefaultPreprocessor,
    WeekdayRecurrence,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The DSNY geocoder names each service's weekdays ("Monday,Wednesday,Friday")
# rather than dates; each is projected weekly from its next occurrence.


@final
class Source(BaseSource):
    TITLE = "New York City"
    DESCRIPTION = "Source for New York City, US."
    URL = "https://www.nyc.gov"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"address": "120-55 Queens Blvd, Kew Gardens, NY 11424"},
        "Test_002": {"address": "1 W 72nd St, New York, NY 10023"},
    }

    PARAMS = (street_address(),)

    retrieve = HttpGetRetriever(
        url="https://dsnypublic.nyc.gov/dsny/api/geocoder/DSNYCollection",
        params=lambda address, **_: {"address": address},
    )
    parse = parsers.JsonParser()
    preprocess = Compose(
        DefaultPreprocessor(),
        WeekdayRecurrence(
            day={
                "RegularCollectionSchedule": "Trash",
                "RecyclingCollectionSchedule": "Recycling",
                "OrganicsCollectionSchedule": "Composting",
                "BulkPickupCollectionSchedule": "Large items",
            }
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Trash": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Composting": wt.ORGANIC,
            "Large items": wt.BULKY_WASTE,
        }
    )
