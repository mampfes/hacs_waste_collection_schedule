from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service import SidecLu
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "SIDEC"
    DESCRIPTION = "Source for SIDEC waste collection."
    URL = "https://www.sidec.lu"
    COUNTRY = "lu"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Parc Hosingen": {"commune": "Parc Hosingen"},
        "Mersch (old style with id)": {"commune": "Mersch (2611)"},
    }

    PARAMS = (text_field("commune", label="Commune"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your commune as listed on the SIDEC website, e.g. 'Mersch'. "
            "An unknown commune lists the valid ones."
        ),
    }

    retrieve = SidecLu.retriever
    parse = SidecLu.SidecParser()

    transform = ICSTransformer(
        type_value_map={
            "menager": wt.GENERAL_WASTE,
            "bio": wt.ORGANIC,
            "papier": wt.PAPER,
            "verre": wt.GLASS,
            "encombrants": wt.BULKY_WASTE,
        }
    )
