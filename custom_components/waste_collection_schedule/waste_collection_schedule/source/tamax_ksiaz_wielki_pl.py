"""TAMAX household collection calendars for Gmina Książ Wielki."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfRuledTable import RuledTableParser
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.service.TamaxMonthGrid import MonthGrid
from waste_collection_schedule.transformers import ICSTransformer

_PAGE = f"{URL}/harmonogramy/malopolskie/gmina-ksiaz-wielki/"
_AREAS = {
    "Książ Wielki, Wielka Wieś": r"^Książ Wielki Wielka Wieś",
    "Cisie, Łazy, Mianocice, Rzędowice, Cisia Wola": r"^Cisie",
    "Moczydło, Głogowiany-Stara Wieś, Głogowiany-Wrzosy, Konaszówka, Krzeszówka": r"^Moczydło",
    "Boczkowice, Książ Mały, Książ Mały Kolonia, Trzonów, Zaryszyn": r"^Boczkowice",
    "Antolka, Częstoszowice, Giebułtów, Małoszów, Tochołów": r"^Antolka",
}
_TYPES = {
    "Odpady zmieszane i segregowane": [wt.GENERAL_WASTE, wt.RECYCLABLES],
    "Odpady zmieszane i bio": [wt.GENERAL_WASTE, wt.ORGANIC],
    "Odpady wielkogabarytowe": [wt.BULKY_WASTE, wt.TEXTILES],
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Książ Wielki)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Książ Wielki."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Książ Wielki"),)
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.BULKY_WASTE,
        wt.TEXTILES,
    ]
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not an area"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Household calendar area"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Open Gmina Książ Wielki (mieszkańcy) at "
            "https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-ksiaz-wielki/ and "
            "select the village group your village appears in. The current half-year "
            "calendar is found on the page each time, so a new upload is picked up "
            "without a change. Mixed waste is collected together with either the "
            "segregated waste or the bio waste; the bulky waste collection also takes "
            "car tyres and textiles. Apartment blocks (BLOKI) are only given as weekday "
            "rules without dates and are not supported."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _PAGE,
                pick=CalendarLink(
                    "Książ Wielki",
                    dict.fromkeys(_AREAS, "Harmonogram Książ Wielki"),
                    match_label=True,
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = RuledTableParser(min_cells=50, merged_cells=True)
    preprocess = MonthGrid(
        _TYPES,
        year_pattern=r"(?i)(?:POŁROCZE|ROKU?)\W{0,3}(20\d\d)",
        areas=_AREAS,
        area_in="row",
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
