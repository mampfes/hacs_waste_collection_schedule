from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.dienten.gv.at"


@final
class Source(BaseSource):
    TITLE = "Dienten am Hochkönig"
    DESCRIPTION = "Waste collection schedule for Dienten am Hochkönig, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    # The vocabulary this feed actually produces, derived by replaying the
    # recorded cassette. Declared explicitly because most of these labels are
    # resolved by the shared vocabulary rather than listed in type_value_map,
    # so the auto-derived set would be incomplete.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
    ]

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

    # The household/trade suffixes are Dienten's own naming, so they belong
    # here rather than in the shared vocabulary: "Altpapier Haushalt" is the
    # household counterpart of the "Gewerbe" rounds already listed. Every other
    # label (Restmüll, Biotonne, Gelbe Tonne, Gelber Sack) is classified by the
    # shared vocabulary.
    #
    # "Recyclinghof" is the recycling centre's opening days, 22 of the 85
    # entries this source published, and not a collection. It is dropped for
    # the reason set out in angern_gv_at: a depot being open is not a bin going
    # out, and mapping it to RECYCLABLES would claim that it was.
    transform = ICSTransformer(
        type_value_map={
            "Papier Gewerbe": wt.PAPER,
            "Karton Gewerbe": wt.PAPER,
            "Altpapier Haushalt": wt.PAPER,
            "Recyclinghof": None,
        },
    )
