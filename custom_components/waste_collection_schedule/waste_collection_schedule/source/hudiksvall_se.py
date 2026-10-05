import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


def _collection_date(record) -> "datetime.date | None":
    """A collection named by ISO year, week and Swedish weekday ("Tisdag")."""
    weekday = recurrence.weekday(record["day"])
    if weekday is None:
        return None
    return datetime.date.fromisocalendar(record["year"], record["week"], weekday + 1)


@final
class Source(BaseSource):
    TITLE = "Hudiksvall"
    DESCRIPTION = "Source for Hudiksvall."
    URL = "https://www.hudiksvall.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.FOOD_WASTE, wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Kommunhuset": {"address": "Trädgårdsgatan 4 Hudiksvall"},
    }

    PARAMS = (street_address(),)

    retrieve = HttpGetRetriever(
        url="https://gis.hudiksvall.se/origoserver/EDPFuture",
        params=lambda address, **_: {"address": address},
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key=_collection_date,
        type_key="type",
        type_value_map={
            "Matavfall": wt.FOOD_WASTE,
            "Restavfall": wt.GENERAL_WASTE,
        },
    )
