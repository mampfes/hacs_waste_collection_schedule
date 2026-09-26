from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "South Gloucestershire Council"
    DESCRIPTION = "Source script for southglos.gov.uk"
    URL = "https://southglos.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "643346"},
        "Test_002": {"uprn": "641084"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://api.southglos.gov.uk/wastecomp/GetCollectionDetails",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    parse = parsers.JsonParser("value", raise_for_status=True)
    # A service with no collection scheduled has no next date and is skipped.
    transform = JsonTransformer(
        date_key=lambda record: (record.get("hso_nextcollection") or "")[:10],
        type_key="hso_servicename",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Garden": wt.GARDEN_WASTE,
            # Absorbent hygiene products (nappies, incontinence pads).
            "AHP": wt.GENERAL_WASTE,
        },
    )
