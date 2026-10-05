from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street_address
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


def _content(record) -> str:
    """The container's content type. A compartment of a shared bin is listed
    as "Kärl 1" / "Kärl 2" and names its content at the end of the container
    type instead ("Kärl 370 liter kärl 1 restavfall")."""
    content = str(record.get("contentType") or "")
    if content.startswith("Kärl"):
        return str(record.get("containerType") or content).split()[-1]
    return content


@final
class Source(BaseSource):
    TITLE = "SRV Återvinning"
    DESCRIPTION = "Source for SRV återvinning AB, Sweden"
    URL = "https://www.srvatervinning.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Skansvägen": {"address": "Skansvägen"},
        "Tullinge 1": {"address": "Hanvedens allé 78"},
        "Tullinge 2": {"address": "Skogsmulles Väg 22"},
        "Skolvägen": {"address": "Skolvägen 10", "city": "TUNGELSTA"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "Nowhere 999"},
    }

    PARAMS = (street_address(), city(optional=True))

    retrieve = HttpGetRetriever(
        url="https://www.srvatervinning.se/rest-api/core/sewagePickup/search",
        params=lambda address, city=None, **_: {
            "query": address,
            "city": (city or "").upper(),
        },
    )
    parse = parsers.JsonParser("results")
    # Each result carries its containers, each container its pickup dates.
    preprocess = Compose(
        ExplodeList("containers"),
        ExplodeList("calendars", into="calendar"),
    )
    transform = JsonTransformer(
        date_key=lambda record: record["calendar"]["startDate"],
        type_key=_content,
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Papper och Plast": wt.RECYCLABLES,
        },
    )
