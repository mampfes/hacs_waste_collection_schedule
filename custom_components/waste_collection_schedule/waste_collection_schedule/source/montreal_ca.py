from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import FanOutRetriever, Request
from waste_collection_schedule.service.MontrealCollectes import (
    TARGETS,
    MontrealCollectesParser,
)
from waste_collection_schedule.transformers import RowTransformer

# Montreal does not offer an iCal/Webcal subscription method. The GeoJSON files
# give sector-specific English prose, read in ``service/MontrealCollectes.py``.
# Not every sector follows the same structure, so this is a best effort until
# the city publishes dated data.


@final
class Source(BaseSource):
    TITLE = "Montreal (QC)"
    DESCRIPTION = "Source script for montreal.ca/info-collectes"
    URL = "https://montreal.ca/info-collectes"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Lasalle": {"sector": "LSL4"},
        "Mercier-Hochelaga": {
            "sector": "MHM_42-5_A",
            "food": "MHM-42-S",
            "recycling": "MHM-42-S",
        },
        "Ahuntsic": {"sector": "AC-2"},
        "Rosemont": {
            "sector": "RPP-RE-22-OM",
            "recycling": "RPP_MR-5",
            "food": "RPP-RE-22-RA",
            "green": "RPP-RE-22-RV",
            "bulky": "RPP-REGIE-22",
        },
        "Pierrefonds-Roxboro": {"sector": "PIRO-1"},
    }

    PARAMS = (
        text_field("sector", "Waste sector"),
        text_field("recycling", "Recycling sector", optional=True),
        text_field("bulky", "Bulky items sector", optional=True),
        text_field("food", "Food waste sector", optional=True),
        text_field("green", "Greens and leafs sector", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Download the Montreal GeoJSON file "
            "(https://donnees.montreal.ca/dataset/collecte-des-ordures-menageres), "
            "open it on https://geojson.io/ and find your sector on the map. "
            "Recycling, bulky items, food waste and greens use the waste sector "
            "unless you give a different one."
        ),
    }

    retrieve = FanOutRetriever(
        targets=lambda source, context: TARGETS,
        fetch=Request(lambda target, *_, **__: target, timeout=60),
    )
    parse = MontrealCollectesParser()
    transform = RowTransformer(
        type_value_map={
            "Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Green": wt.GARDEN_WASTE,
            "Bulky": wt.BULKY_WASTE,
        }
    )
