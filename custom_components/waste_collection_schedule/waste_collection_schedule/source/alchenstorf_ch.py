from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.IWeb import (
    AbfalldatenRows,
    abfalldaten_parser,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Alchenstorf"
    DESCRIPTION = "Source for 'Alchenstorf, CH'"
    URL = "https://www.alchenstorf.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {"TEST": {}}

    PARAMS = ()

    retrieve = HttpGetRetriever(url="https://www.alchenstorf.ch/abfalldaten")
    parse = abfalldaten_parser()
    # A collection over several days (the paper and cardboard drives) is one
    # collection per day.
    preprocess = AbfalldatenRows(expand_ranges=True)
    transform = ICSTransformer(
        type_value_map={
            "Grünabfuhr Alchenstorf": wt.GARDEN_WASTE,
            "Kehrichtabfuhr Alchenstorf": wt.GENERAL_WASTE,
            "Kartonsammlung Alchenstorf": wt.PAPER,
            "Papiersammlung Alchenstorf": wt.PAPER,
            "Alteisenabfuhr Alchenstorf": wt.RECYCLABLES,
        }
    )
