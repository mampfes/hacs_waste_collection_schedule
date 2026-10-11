from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.parsers import EachResponse
from waste_collection_schedule.service.Localcities import (
    CalendarParser,
    PlaceRows,
    calendar_retriever,
    calendar_url,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Grenchen (CH)"
    DESCRIPTION = "Source for waste collection in Grenchen, Switzerland. Deprecated: use localcities_ch instead."
    URL = "https://www.grenchen.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.CARTONS,
        wt.PAPER,
        wt.GLASS,
        wt.METAL,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Zone Ost": {"zone": "Zone Ost"},
        "Zone West": {"zone": "Zone West"},
    }

    PARAMS = (dropdown("zone", ["Zone Ost", "Zone West"], "Zone"),)

    HOWTO: ClassVar[dict] = {
        "en": "This source is deprecated. Please use 'localcities.ch' instead with municipality='grenchen' and municipality_id='3533'.",
        "de": "Diese Quelle ist veraltet. Bitte verwenden Sie 'localcities.ch' mit municipality='grenchen' und municipality_id='3533'.",
    }

    retrieve = calendar_retriever(calendar_url("grenchen", "3533"))
    parse = EachResponse(CalendarParser())
    preprocess = PlaceRows("zone")
    transform = ICSTransformer(
        type_value_map={
            "Grünabfälle": wt.GARDEN_WASTE,
            "Karton": wt.CARTONS,
            "Altpapier": wt.PAPER,
            "Altglas": wt.GLASS,
            "Altmetall": wt.METAL,
        }
    )
