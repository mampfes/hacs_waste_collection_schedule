from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, text_field
from waste_collection_schedule.preprocessors import DateFields
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer


def _query(suburb: str, split_suburb: str | None = None, **_) -> dict:
    """The open-data filter: suburbs are upper case, split names capitalised."""
    query = {"suburb": suburb.upper()}
    if split_suburb:
        query["split_suburb"] = split_suburb.capitalize()
    return query


@final
class Source(BaseSource):
    TITLE = "Australian Capital Territory (ACT)"
    DESCRIPTION = "Source script for Australian Capital Territory (ACT)."
    URL = "https://www.cityservices.act.gov.au/recycling-and-waste"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Bruce": {"suburb": "Bruce"},
        "Amaroo": {"suburb": "amaroo"},
        "Charnwood Thursday": {"suburb": "CHARNWOOD", "split_suburb": "Thursday"},
        "Charnwood Tuesday": {"suburb": "CHARNWOOD", "split_suburb": "Tuesday"},
        "Dunlop North": {"suburb": "DUNLOP", "split_suburb": "NORTH"},
        "Dunlop South": {"suburb": "DUNLOP", "split_suburb": "south"},
    }

    PARAMS = (
        district("suburb"),
        text_field("split_suburb", "Split Suburb", optional=True),
    )

    retrieve = HttpGetRetriever(
        url="https://www.data.act.gov.au/resource/jzzy-44un.json",
        params=_query,
    )
    # One record per (split) suburb; a suburb that is split without a split
    # given answers each half, of which the first is the one the legacy
    # source used.
    parse = parsers.JsonParser(0)
    preprocess = DateFields(
        fields={
            "garbage_pickup_date": "Garbage",
            "recycling_pickup_date": "Recycle",
            "next_greenwaste_date": "Organic",
        },
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
    transform = ICSTransformer(
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycle": wt.RECYCLABLES,
            "Organic": wt.GARDEN_WASTE,
        }
    )
