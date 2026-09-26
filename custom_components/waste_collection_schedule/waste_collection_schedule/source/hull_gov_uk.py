from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import FlattenGroups
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Hull City Council"
    DESCRIPTION = "Source for Hull City Council."
    URL = "https://hull.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "21095794": {"uprn": 21095794},
        "21009164": {"uprn": "21009164"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.hull.gov.uk/ajax/bin-collection",
        params=lambda uprn, **_: {"bindate": uprn},
        headers={"Referer": "https://www.hull.gov.uk"},
    )
    parse = parsers.JsonParser()
    # The reply is a list wrapping the list of collections.
    preprocess = FlattenGroups()
    transform = JsonTransformer(
        date_key="next_collection_date",
        type_key="collection_type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Black Bin": wt.GENERAL_WASTE,
            "Blue Bin": wt.RECYCLABLES,
            "Brown Bin": wt.ORGANIC,
            "Bulky Bin": wt.BULKY_WASTE,
        },
    )
