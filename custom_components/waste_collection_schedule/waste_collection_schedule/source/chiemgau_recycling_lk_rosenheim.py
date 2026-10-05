from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# The API answers a bare list of dates; Chiemgau Recycling empties only the
# paper bin ("blaue Tonne").


@final
class Source(BaseSource):
    TITLE = "Chiemgau Recycling - Landkreis Rosenheim"
    DESCRIPTION = "Source script for paper waste collection in Landkreis Rosenheim area"
    URL = "https://chiemgau-recycling.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.PAPER]

    TEST_CASES: ClassVar[dict] = {"Bruckmühl 1": {"district": "Bruckmühl 1"}}

    PARAMS = (district(),)

    retrieve = HttpGetRetriever(
        url="https://blauetonne.stkn.org/lk_rosenheim",
        params=lambda district, **_: {"district": district},
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key=lambda record: str(record)[:10],
        type_key=lambda _record: "Papiertonne",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={"Papiertonne": wt.PAPER},
    )
