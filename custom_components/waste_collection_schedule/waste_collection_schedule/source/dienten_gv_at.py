from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import PAPER

_BASE_URL = "https://www.dienten.gv.at"


@final
class Source(BaseSource):
    TITLE = "Dienten am Hochkönig"
    DESCRIPTION = "Waste collection schedule for Dienten am Hochkönig, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        # no input required as the waste collection site (dienten.gv.at) does
        # not have any address specific requirement
        "Dorf 53": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "blnr": "",
            "gnr_search": "0",
            "menuonr": "218643352",
        },
    )
    parse = RiSKommunalParser()

    # Only the commercial-collection labels (Gewerbe suffix) need an explicit
    # entry; every other label (Restmüll, Biotonne, Gelbe Tonne, Gelber Sack)
    # is classified by the shared vocabulary.
    transform = ICSTransformer(
        type_value_map={
            "Papier Gewerbe": PAPER,
            "Karton Gewerbe": PAPER,
        },
    )
