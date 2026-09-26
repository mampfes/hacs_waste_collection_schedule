from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# The skyCMS app backend; the key is the app's own public one.
_HEADERS = {
    "x-skycms-key": "5d0123032115904c9d4ff70522405e60",
    "x-skycms-type": "iOS",
    "x-skycms-device": "04C977DF-F4BB-4541-AEF2-EB2F454CB4D2",
}


@final
class Source(BaseSource):
    TITLE = "Gmina Miękinia"
    DESCRIPTION = "Source for Gmina Miękinia, Poland"
    URL = "https://api.skycms.com.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {"Brzezina": {"location_id": 8}}

    PARAMS = (location_id(),)

    retrieve = HttpGetRetriever(
        url=lambda location_id, **_: (
            f"https://api.skycms.com.pl/api/v1/rest/garbage/disposals/{location_id}"
        ),
        headers=_HEADERS,
    )
    parse = parsers.JsonParser("data", "garbage_kinds")
    # Each kind lists its collection days.
    preprocess = ExplodeList("disposals", into="disposal")
    transform = JsonTransformer(
        date_key=lambda record: record["disposal"]["id"],
        type_key="name",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Zmieszane": wt.GENERAL_WASTE,
            "Bioodpady": wt.ORGANIC,
            "Papier": wt.PAPER,
            "Szkło": wt.GLASS,
            "Tworzywa sztuczne": wt.RECYCLABLES,
            "Wielkogabaryty": wt.BULKY_WASTE,
        },
    )
