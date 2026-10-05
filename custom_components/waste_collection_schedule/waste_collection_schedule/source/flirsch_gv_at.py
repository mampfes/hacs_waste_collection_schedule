from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.flirsch.gv.at"


@final
class Source(BaseSource):
    TITLE = "Gemeinde Flirsch"
    DESCRIPTION = "Source for Gemeinde Flirsch, Tyrol, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    # The vocabulary this feed actually produces, derived by replaying the
    # recorded cassette.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    # One whole-municipality calendar, no street selection. These ids are the
    # ones the municipality's own Abfallkalender page links to.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "detailonr": "226421647",
            "menuonr": "226398050",
            "typids": "226421647",
        },
    )
    parse = RiSKommunalParser()

    # The frequency suffix breaks the exact-match resolution of "Restmüll".
    transform = ICSTransformer(
        type_value_map={
            "Restmüll 2-wöchig": wt.GENERAL_WASTE,
        },
    )
