from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import DateFields
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_parse = date_parsers.for_format("%Y-%m-%dT%H:%M:%S")


@final
class Source(BaseSource):
    TITLE = "Hamilton City Council"
    DESCRIPTION = "Source script for Hamilton City Council"
    URL = "https://www.fightthelandfill.co.nz/"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "1 Hamilton Parade": {"address": "1 Hamilton Parade"},
        "221b fox Street": {"address": "221b fox Street"},
    }

    PARAMS = (street_address(),)

    retrieve = HttpGetRetriever(
        url="https://api2.hcc.govt.nz/FightTheLandFill/get_Collection_Dates",
        params=lambda address, **_: {"address_string": address},
    )
    parse = parsers.JsonParser()
    # One record per address, the next date of each bin in its own field.
    preprocess = DateFields(
        fields={"RedBin": "Rubbish", "YellowBin": "Recycling"},
        parse_date=lambda value: _parse(value) if value else None,
    )
    transform = ICSTransformer(
        type_value_map={"Rubbish": wt.GENERAL_WASTE, "Recycling": wt.RECYCLABLES}
    )
