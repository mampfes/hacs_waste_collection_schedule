from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service import ValorluxLu
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Valorlux"
    DESCRIPTION = "Source for Valorlux waste collection."
    URL = "https://www.valorlux.lu"
    COUNTRY = "lu"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Mersch": {"commune": "Mersch"},
        "Luxembourg City (Tour 1)": {"commune": "Luxembourg", "zone": "Tour 1"},
        "Parc Hosingen": {"commune": "Parc Hosingen"},
        "Dudelange (Tournée Lundi)": {
            "commune": "Dudelange",
            "zone": "Tournée Lundi",
        },
    }

    PARAMS = (
        text_field("commune", label="Commune"),
        text_field("zone", label="Zone / tour", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your commune as listed on the Valorlux calendar page, e.g. "
            "'Mersch'. Communes with several collection tours (e.g. 'Luxembourg' "
            "with 'Tour 1') also need the zone; a missing or wrong value lists "
            "the valid ones."
        ),
    }

    retrieve = ValorluxLu.retriever
    parse = ValorluxLu.ValorluxParser()

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%y"),
        type_value_map={ValorluxLu.LABEL: wt.RECYCLABLES},
    )
