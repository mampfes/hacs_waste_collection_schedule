from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.transformers import JsonTransformer

_ZONES = ["A", "B", "C", "D", "E", "F", "G", "H", "GUF"]

_TYPE_MAP = {
    "Kehrichtabfuhr": wt.GENERAL_WASTE,
    "Grünabfuhr": wt.ORGANIC,
    "Papierabfuhr": wt.PAPER,
    "Grobsperrgut": wt.BULKY_WASTE,
    "Häckseldienst": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Basel-Stadt"
    DESCRIPTION = "Source for waste collection schedule of Basel-Stadt, Switzerland."
    URL = "https://data.bs.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Zone A": {"zone": "A"},
        "Zone B": {"zone": "B"},
    }

    PARAMS = (dropdown("zone", _ZONES, label="Zone"),)

    HOWTO: ClassVar[dict] = {
        "en": "Your waste collection zone (A-H or GUF).",
        "de": "Ihre Abfuhrzone (A-H oder GUF).",
    }

    retrieve = retrievers.YearlyRetriever(
        fetch=retrievers.Request(
            "https://data.bs.ch/api/records/1.0/search/",
            params=lambda year, context, zone, **_: {
                "dataset": "100096",
                "rows": 500,
                "refine.zone": zone,
                "q": f"termin>={year}-01-01 AND termin<={year}-12-31",
                "sort": "termin",
            },
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser("records"))
    transform = JsonTransformer(
        date_key=lambda record: record["fields"]["termin"],
        type_key=lambda record: record["fields"]["art"],
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=_TYPE_MAP,
    )
