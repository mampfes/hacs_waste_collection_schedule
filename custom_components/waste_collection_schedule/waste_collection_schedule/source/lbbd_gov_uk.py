from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "London Borough of Barking and Dagenham"
    DESCRIPTION = "Source for London Borough of Barking and Dagenham."
    URL = "https://www.lbbd.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "100 Heathway": {"uprn": "100014033"},
        "40 Porters Avenue": {"uprn": "100024629"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: f"https://www.lbbd.gov.uk/rest/bin/{uprn}",
    )
    parse = parsers.JsonParser("results")
    # Each bin carries its next date and a list of the following ones.
    preprocess = ExplodeList("nextcollection", "futurecollections", into="date")
    transform = JsonTransformer(
        date_key="date",
        type_key="bin_type",
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map={
            "Grey-Household": wt.GENERAL_WASTE,
            "Brown-Recycling": wt.RECYCLABLES,
            "Green-Garden": wt.GARDEN_WASTE,
        },
    )
