from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "London Borough of Harrow"
    DESCRIPTION = "Source for London Borough of Harrow."
    URL = "https://www.harrow.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "1 Dudley Gardens": {"uprn": "100021261713"},
        "FLAT 3, 12, LOWER ROAD, HARROW, HA2 0DA": {"uprn": 10070270427},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.harrow.gov.uk/ajax/bins",
        # The council's UPRNs are twelve digits, zero-padded.
        params=lambda uprn, **_: {"u": str(uprn).zfill(12)},
    )
    parse = parsers.JsonParser("results", "collections", "next", raise_for_status=True)
    transform = JsonTransformer(
        date_key=lambda record: (record.get("eventTime") or "")[:10],
        type_key="binType",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "RESIDUAL": wt.GENERAL_WASTE,
            "RECYCLABLES": wt.RECYCLABLES,
            "GARDEN": wt.GARDEN_WASTE,
            "FOOD": wt.FOOD_WASTE,
        },
    )
