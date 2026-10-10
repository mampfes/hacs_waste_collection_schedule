from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.service import SicaLu
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "SICA"
    DESCRIPTION = "Source script for sica.lu served municipalities"
    URL = "https://sica.lu"
    COUNTRY = "lu"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GLASS,
        wt.PAPER,
        wt.OTHER,
        wt.TEXTILES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Habscht": {"municipality": "habscht"},
        "Steinfort": {"municipality": "Steinfort"},
    }

    PARAMS = (municipality(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the name of your municipality as listed by SICA, e.g. "
            "'Steinfort', 'Habscht' or 'Mamer'. A wrong name lists the valid ones."
        ),
    }

    retrieve = SicaLu.retriever
    parse = SicaLu.SicaParser()

    transform = JsonTransformer(
        date_key="date",
        type_key=lambda record: record["pickup_type"]["name"]["en"],
        type_value_map={
            "Residual waste": wt.GENERAL_WASTE,
            "Valorlux - blue bag": wt.RECYCLABLES,
            "Organic waste": wt.ORGANIC,
            "Glass": wt.GLASS,
            "Paper /Carton": wt.PAPER,
            "Scrap and electrical appliances": wt.OTHER,
            "Clothing and Shoes": wt.TEXTILES,
            "Hedges, Shrubs and Trees": wt.GARDEN_WASTE,
            "Bulky waste": wt.BULKY_WASTE,
        },
        parse_date=date_parsers.for_format("%Y-%m-%d %H:%M:%S"),
        color_key=lambda record: record["pickup_type"]["color"],
        carry_raw_label=True,
    )
