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
    "rest/mad": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
    "papir/pap - metal/plast/drikkekarton": [
        wt.PAPER,
        wt.METAL,
        wt.PLASTIC,
        wt.CARTONS,
    ],
    "Miljøkasse til farligt affald": wt.HAZARDOUS,
}


def _fraction(description: str) -> str:
    """``"190 l beh. rest/mad - ny"`` -> ``"rest/mad"``."""
    text = re.sub(r"^\d+\s*l\s+beh\.\s+", "", description, flags=re.IGNORECASE)
    return re.sub(r"\s+-\s+ny$", "", text, flags=re.IGNORECASE).strip()


@final
class Source(BaseSource):
    TITLE = "Kalundborg Kommune"
    DESCRIPTION = "Source for Kalundborg Kommune waste collection schedule"
    URL = "https://kalundborg.dk"
    COUNTRY = "dk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.METAL,
        wt.PLASTIC,
        wt.CARTONS,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestCase1": {"id": "00008d18-0002-0001-4164-647265737320"},
        "TestCase2": {"id": "00006643-0002-0001-4164-647265737320"},
    }

    PARAMS = (text_field("id", "Address ID"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "To get your address ID: go to "
            "https://kalundborg.infovision.dk/public/selectaddress and search for "
            "your address. You will find the ID in the URL of the address page, "
            "e.g. https://kalundborg.infovision.dk/public/address/"
            "00006ac8-0002-0001-4164-647265737320, a UUID like "
            "`00006ac8-0002-0001-4164-647265737320`."
        ),
    }

    retrieve = container_retriever("kalundborg")
    parse = ContainerParser()
    transform = RowTransformer(clean=_fraction, type_value_map=_TYPE_MAP)
