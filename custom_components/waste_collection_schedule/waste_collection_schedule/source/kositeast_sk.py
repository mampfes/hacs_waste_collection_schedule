from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.service import KositCalendar as kosit
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/"


@final
class Source(BaseSource):
    TITLE = "KOSIT EAST"
    DESCRIPTION = "Source for KOSIT EAST waste collection."
    URL = "https://kositeast.sk"
    COUNTRY = "sk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.HAZARDOUS,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Adidovce": {"town": "Adidovce"},
        "Andrejová": {"town": "Andrejová"},
    }

    PARAMS = (municipality("town"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Find your town on https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/"
            " and enter it exactly as it appears in the link."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_INDEX_URL, pick=kosit.pdf_link),),
        url=lambda *keys, **_: keys[-1],
    )
    parse = kosit.CalendarParser(
        columns=6,
        rows=2,
        max_rect_width=0.026,
        match_horizontal_overlap=False,
        year_pattern=r"ROK\s+(\d{4})",
    )
    transform = ICSTransformer(
        type_value_map={
            kosit.GENERAL: wt.GENERAL_WASTE,
            kosit.PLASTICS: wt.RECYCLABLES,
            kosit.GLASS: wt.GLASS,
            kosit.PAPER: wt.PAPER,
            kosit.OIL: wt.FOOD_WASTE,
            kosit.HAZARDOUS: wt.HAZARDOUS,
        }
    )
