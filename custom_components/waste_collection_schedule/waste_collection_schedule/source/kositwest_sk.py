from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.service import KositCalendar as kosit
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = (
    "https://kositwest.sk/sluzby/zber-komunalneho-odpadu-a-triedenych-zloziek-z-obci-"
    "a-samosprav/harmonogramy-zberu-odpadu-v-obciach/"
)


@final
class Source(BaseSource):
    TITLE = "KOSIT WEST"
    DESCRIPTION = "Source for KOSIT WEST waste collection."
    URL = _INDEX_URL
    COUNTRY = "sk"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@mynameisdominik"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Vieska": {"town": "Vieska"},
        "Sap": {"town": "Sap"},
        "Michal na Ostrove": {"town": "Michal na Ostrove"},
    }

    PARAMS = (municipality("town"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Find your town on the KOSIT WEST website and enter it exactly as it "
            "appears in the link."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_INDEX_URL, pick=kosit.pdf_link),),
        url=lambda *keys, **_: keys[-1],
    )
    parse = kosit.CalendarParser(
        columns=3,
        rows=4,
        max_rect_width=0.04,
        match_horizontal_overlap=True,
        year_pattern=r"\b(20\d{2})\b",
        extra_colours={
            (0.573, 0.816, 0.314): kosit.GLASS,
            (0.557, 0.663, 0.859): kosit.PAPER,
        },
        ignored=[(1.0, 1.0, 1.0)],
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
