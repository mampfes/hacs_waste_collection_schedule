from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Ealing Council"
    DESCRIPTION = "Source for Ealing Council."
    URL = "https://www.ealing.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "11 LOTHAIR ROAD, EALING, LONDON, W5 4TA": {"uprn": 12081500},
        "53 CREIGHTON ROAD, EALING, LONDON, W5 4SH": {"uprn": "12082293"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpPostRetriever(
        url="https://www.ealing.gov.uk/site/custom_scripts/WasteCollectionWS/home/FindCollection",
        data=lambda uprn, **_: {"UPRN": uprn},
    )
    parse = parsers.JsonParser("param2", raise_for_status=True)
    # Each service lists all its dates.
    preprocess = ExplodeList("collectionDate", into="date")
    transform = JsonTransformer(
        date_key="date",
        type_key="Service",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "BLACK RUBBISH WHEELIE BIN": wt.GENERAL_WASTE,
            "BLUE RECYCLING WHEELIE BIN": wt.RECYCLABLES,
            "FOOD BOX": wt.FOOD_WASTE,
            "GREEN GARDEN WASTE WHEELIE BIN": wt.GARDEN_WASTE,
        },
    )
