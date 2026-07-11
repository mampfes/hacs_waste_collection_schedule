from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.st.margarethen.salzburg.at"


@final
class Source(BaseSource):
    TITLE = "St. Margarethen im Lungau"
    DESCRIPTION = "Waste collection schedule for St. Margarethen im Lungau, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "St. Margarethen im Lungau": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "blnr": "",
            "gnr_search": "0",
            "menuonr": "218716164",
        },
    )
    parse = RiSKommunalParser()

    # Every label here carries an "Abholung " (collection) prefix or, for
    # bulky waste, an "-abfuhr" suffix, so none resolve against the shared
    # vocabulary verbatim; all six are mapped explicitly.
    transform = ICSTransformer(
        type_value_map={
            "Abholung BIO-Tonne": ORGANIC,
            "Abholung Gelber Sack": RECYCLABLES,
            "Abholung Hausmüll": GENERAL_WASTE,
            "Abholung Altpapier": PAPER,
            "Abholung Altglas": GLASS,
            "Sperrmüllabfuhr": BULKY_WASTE,
        },
    )
