from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Betzdorf"
    DESCRIPTION = "Source for Betzdorf, Luxembourg waste collection."
    URL = "https://www.betzdorf.lu"
    COUNTRY = "lu"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {"Betzdorf": {}}

    PARAMS = ()

    retrieve = HttpGetRetriever(url="https://www.betzdorf.lu/fr/waste")
    parse = parsers.JsonParser()
    # Each waste type lists all its dates.
    preprocess = ExplodeList("dates", into="date")
    transform = JsonTransformer(
        date_key=lambda record: (record["date"].get("dateStart") or "")[:10],
        type_key="slug",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "dechets-menagers-hausmull-exception": wt.GENERAL_WASTE,
            "dechets-biodegradables-biomull-exception": wt.ORGANIC,
            "dechets-verts-grunschnitt": wt.GARDEN_WASTE,
            "dechets-encombrants-sperrmull": wt.BULKY_WASTE,
            "valorlux": wt.RECYCLABLES,
            "verre-papiers-altglas-altpapier": [wt.GLASS, wt.PAPER],
            # The recycling park's opening days, not a collection.
            "centre-de-ressources-recyclingpark-superdreckskescht": None,
        },
    )
