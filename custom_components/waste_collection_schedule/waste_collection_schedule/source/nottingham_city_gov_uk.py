import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


def _within_a_year(record, _source) -> bool:
    # The API sometimes lists collections far in the future; keep the next year.
    day = datetime.date.fromisoformat(record["collectionDate"][:10])
    return day <= datetime.date.today() + datetime.timedelta(days=365)


@final
class Source(BaseSource):
    TITLE = "Nottingham City Council"
    DESCRIPTION = (
        "Source for nottinghamcity.gov.uk services for the city of Nottingham, UK."
    )
    URL = "https://nottinghamcity.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Douglas Rd, Nottingham NG7 1NW": {"uprn": "100031540175"},
        "Harlaxton Drive, Nottingham, NG7 1JE": {"uprn": "100031553830"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: (
            f"https://geoserver.nottinghamcity.gov.uk/bincollections2/api/collection/{uprn}"
        ),
    )
    parse = parsers.JsonParser("nextCollections")
    preprocess = RowFilter(_within_a_year)
    transform = JsonTransformer(
        date_key=lambda record: record["collectionDate"][:10],
        type_key="collectionType",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
            "Food23L": wt.FOOD_WASTE,
            "Food23L_bags": wt.FOOD_WASTE,
        },
    )
