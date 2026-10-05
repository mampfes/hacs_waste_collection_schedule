from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "West Northamptonshire council"
    DESCRIPTION = "Source for West Northamptonshire council."
    URL = "https://www.westnorthants.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "28058314": {"uprn": 28058314},
        "15049111": {"uprn": "15049111"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: (
            f"https://api.westnorthants.digital/openapi/v1/unified-waste-collections/{uprn}"
        ),
    )
    parse = parsers.JsonParser("collectionItems", raise_for_status=True)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "refuse": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "food": wt.FOOD_WASTE,
            "garden": wt.GARDEN_WASTE,
            # Properties without wheelie bins.
            "sacks": wt.GENERAL_WASTE,
            "recycling_boxes": wt.RECYCLABLES,
        },
    )
