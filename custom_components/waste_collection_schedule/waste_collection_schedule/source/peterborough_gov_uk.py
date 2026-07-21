"""Peterborough City Council (peterborough.gov.uk).

Demonstrates: the plain-vanilla ICS shape — a single static GET whose URL is
built from two required params (postcode + UPRN), no session/state/lookup of
any kind. HttpGetRetriever + IcsParser + ICSTransformer do all the work; this
module only supplies the URL template and the waste-type map.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

_ICS_URL = "https://report.peterborough.gov.uk/waste/{post_code}:{uprn}/calendar.ics"


@final
class Source(BaseSource):
    TITLE = "Peterborough City Council"
    DESCRIPTION = "Source for peterborough.gov.uk services for Peterborough."
    URL = "https://peterborough.gov.uk"
    COUNTRY = "uk"

    # UPRN/property-id lookup: a wrong id yields no collections, so surface
    # it as an error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "houseUprn": {"post_code": "PE57AX", "uprn": "100090214774"},
    }

    PARAMS = (
        postcode("post_code"),
        uprn("uprn"),
    )

    retrieve = HttpGetRetriever(
        url=lambda post_code, uprn, **_: _ICS_URL.format(post_code=post_code, uprn=uprn)
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Empty Bin 240L Black": GENERAL_WASTE,
            "Empty Bin 240L Green": RECYCLABLES,
            "Empty Bin 240L Brown": ORGANIC,
        }
    )

    def __init__(self, post_code: str, uprn: str):
        super().__init__(post_code=post_code, uprn=uprn)
