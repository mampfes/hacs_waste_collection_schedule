import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.Infovision import (
    ContainerParser,
    container_retriever,
)
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "rest og madaffald": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
    "pap/papir og glas/metal": [wt.PAPER, wt.GLASS, wt.METAL],
    "plast og mad- og drikkekartoner": [wt.PLASTIC, wt.CARTONS],
    "Farligt affald": wt.HAZARDOUS,
}


def _fraction(description: str) -> str:
    """``"240 L 2-delt beholder til rest og madaffald"`` -> ``"rest og madaffald"``;
    ``"Farligt affald - 21 L"`` -> ``"Farligt affald"``."""
    text = re.sub(r"^\d+\s*L\s+(?:2-delt\s+)?(?:beholder til\s+)?", "", description)
    return re.sub(r"\s+-\s+\d+\s*L$", "", text).strip()


@final
class Source(BaseSource):
    TITLE = "Kolding Kommune"
    DESCRIPTION = "Source for Kolding Kommune waste collection schedule"
    URL = "https://kolding.dk"
    COUNTRY = "dk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.GLASS,
        wt.METAL,
        wt.PLASTIC,
        wt.CARTONS,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestCase1": {"id": "00007b76-0002-0001-4164-647265737320"},
        "TestCase2": {"id": "00007b7c-0002-0001-4164-647265737320"},
    }

    PARAMS = (text_field("id", "Address ID"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://kolding.infovision.dk/public/selectaddress and search "
            "for your address. Your ID is in the URL, e.g. "
            "`00007b8d-0002-0001-4164-647265737320`."
        ),
    }

    retrieve = container_retriever("kolding")
    parse = ContainerParser()
    transform = RowTransformer(clean=_fraction, type_value_map=_TYPE_MAP)
