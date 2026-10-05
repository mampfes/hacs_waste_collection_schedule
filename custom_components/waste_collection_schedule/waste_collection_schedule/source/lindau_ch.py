from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.IWeb import (
    AbfalldatenRows,
    abfalldaten_parser,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Lindau"
    DESCRIPTION = "Source for Lindau waste collection."
    URL = "https://www.lindau.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Tagelswangen": {"city": "Tagelswangen"},
        "Grafstal": {"city": "190"},
    }

    PARAMS = (city(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your village as listed on https://www.lindau.ch/abfalldaten "
            "(Grafstal, Lindau, Tagelswangen or Winterberg)."
        ),
        "de": (
            "Geben Sie Ihren Ortsteil so ein, wie er auf "
            "https://www.lindau.ch/abfalldaten steht (Grafstal, Lindau, "
            "Tagelswangen oder Winterberg)."
        ),
    }

    retrieve = HttpGetRetriever(url="https://www.lindau.ch/abfalldaten")
    parse = abfalldaten_parser()
    preprocess = AbfalldatenRows(area="city")
    transform = ICSTransformer(
        type_value_map={
            "Kehricht": wt.GENERAL_WASTE,
            "Biogene Abfälle (Grüngut)": wt.ORGANIC,
            "Häckseldienst": wt.GARDEN_WASTE,
            "Papier und Karton": wt.PAPER,
            "Altmetalle": wt.RECYCLABLES,
            "Sonderabfall": wt.HAZARDOUS,
        }
    )
