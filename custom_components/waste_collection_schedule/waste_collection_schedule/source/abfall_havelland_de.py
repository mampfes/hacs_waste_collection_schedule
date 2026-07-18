"""Abfallbehandlungsgesellschaft Havelland mbH (abfall-havelland.de).

Demonstrates: a static, param-built ICS GET whose feed needs the extended
``IcsParser`` option (``split_at`` for a combined round listed as one
VEVENT) plus a trailing "- Abholtermin" suffix stripped from every label,
expressed as the transformer's ``clean=``. HttpGetRetriever + IcsParser +
ICSTransformer do all the work; this module only supplies the URL/params and
the waste-type map.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer, label_cleaner
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://www.abfall-havelland.de/ics.php"


@final
class Source(BaseSource):
    TITLE = "Abfallbehandlungsgesellschaft Havelland mbH (abh)"
    DESCRIPTION = "Source for Abfallbehandlungsgesellschaft Havelland mbH."
    URL = "https://abfall-havelland.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Wustermark Drosselgasse": {"ort": "Wustermark", "strasse": "Drosselgasse"},
        "Milow Friedhofstr.": {"ort": "Milow", "strasse": "Friedhofstr."},
        "Falkensee Ahornstr.": {"ort": "Falkensee", "strasse": "Ahornstr."},
        "Falkensee complex street name": {
            "ort": "Falkensee",
            "strasse": "Karl-Marx-Str. (von Friedrich-Hahn-Str. bis Am Schlaggraben)",
        },
    }

    PARAMS = (
        city(field="ort"),
        street(field="strasse"),
    )

    retrieve = HttpGetRetriever(
        url=_API_URL,
        params=lambda ort, strasse, **_: {"city": ort, "street": strasse},
    )
    parse = parsers.IcsParser(split_at=r", ")
    transform = ICSTransformer(
        clean=label_cleaner(strip_suffixes=[" - Abholtermin"]),
        type_value_map={
            "mülltonne": GENERAL_WASTE,
            "bio-tonne": ORGANIC,
            "papier u. pappe": PAPER,
            "gelbe tonne": RECYCLABLES,
        },
    )

    def __init__(self, ort: str, strasse: str):
        super().__init__(ort=ort, strasse=strasse)
