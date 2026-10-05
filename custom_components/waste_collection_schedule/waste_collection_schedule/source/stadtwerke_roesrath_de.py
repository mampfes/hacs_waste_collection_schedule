from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Stadtwerke Rösrath"
    DESCRIPTION = "Source for 'Stadtwerke Rösrath'."
    URL = "https://www.stadtwerke-roesrath.de/service/abfuhrkalender/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {"Ahornweg": {"street": "Ahornweg"}}

    PARAMS = (street(),)

    retrieve = HttpPostRetriever(
        url="https://www.stadtwerke-roesrath.de/wp-admin/admin-ajax.php",
        params={"action": "binalarm_filter"},
        data=lambda street, **_: {"street": street},
        headers={
            "referer": "https://www.stadtwerke-roesrath.de/service/abfuhrkalender/"
        },
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key="start",
        type_key="title",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Restmülltonne": wt.GENERAL_WASTE,
            "Restmülltonne 60l": wt.GENERAL_WASTE,
            "Biotonne": wt.ORGANIC,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Papiertonne": wt.PAPER,
            "Schadstoffmobil": wt.HAZARDOUS,
        },
    )
