from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import PAPER

_BASE_URL = "https://www.klosterneuburg.at"
_SELECTION_URL = (
    "https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/"
    "Muellabfuhrkalender"
)


@final
class Source(BaseSource):
    TITLE = "Stadtgemeinde Klosterneuburg"
    DESCRIPTION = "Source for Stadtgemeinde Klosterneuburg waste collection."
    URL = _SELECTION_URL
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {
        "Kierlinger Straße 10": {
            "street": "Kierlinger Straße",
            "house_number": "10",
        },
        "Adalbert Stifter-Gasse 1": {
            "street": "Adalbert Stifter-Gasse",
            "house_number": "1",
        },
    }

    PARAMS = (
        street("street"),
        house_number("house_number"),
    )

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "226582740",
        },
        strasse_param="street",
        hausnummer_param="house_number",
        selection_url=_SELECTION_URL,
    )
    parse = RiSKommunalParser()

    # "Papiermüll" is not in the shared vocabulary (only "Altpapier"/"Papier"
    # are); Restmüll, Biomüll, Gelber Sack and Sperrmüll all resolve unmapped.
    transform = ICSTransformer(
        type_value_map={
            "Papiermüll": PAPER,
        },
    )

    def __init__(self, street: str, house_number: str):
        super().__init__(street=street, house_number=house_number)
