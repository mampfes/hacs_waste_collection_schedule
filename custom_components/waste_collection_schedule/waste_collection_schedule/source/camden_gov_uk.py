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
    TITLE = "London Borough of Camden"
    DESCRIPTION = "Source for London Borough of Camden."
    URL = "https://www.camden.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Red Lion Street": {"uprn": 5121151},
    }

    PARAMS = (uprn(),)

    retrieve = HttpPostRetriever(
        url="https://recyclingandrubbishcollections.camden.gov.uk/api/getCalendarData",
        json=lambda uprn, **_: {"councilId": "27", "uprn": str(uprn)},
        headers={"x-recaptcha-token": ""},
    )
    parse = parsers.JsonParser(
        "data", raise_for_status=True, expected_values={"message": "OK"}
    )
    preprocess = ExplodeList("records")
    transform = JsonTransformer(
        date_key=lambda record: (record.get("actual_scheduled_date") or "")[:10],
        type_key="service",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Rubbish collection": wt.GENERAL_WASTE,
            "Recycling collection": wt.RECYCLABLES,
            "Food collection": wt.FOOD_WASTE,
            "Garden collection": wt.GARDEN_WASTE,
            "Garden waste collection": wt.GARDEN_WASTE,
            # Older spellings the legacy source also recognised.
            "Domestic refuse collection": wt.GENERAL_WASTE,
            "Domestic DMR collection": wt.RECYCLABLES,
            "Domestic food collection": wt.FOOD_WASTE,
            "Domestic garden collection": wt.GARDEN_WASTE,
            # A record without a service name is not a collection.
            "": None,
        },
    )
