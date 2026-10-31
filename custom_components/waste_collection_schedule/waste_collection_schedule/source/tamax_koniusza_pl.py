"""TAMAX household collection calendars for Gmina Koniusza."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfRuledTable import RuledTableParser
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.service.TamaxMonthGrid import MonthGrid
from waste_collection_schedule.transformers import ICSTransformer

_PAGE = f"{URL}/harmonogramy/malopolskie/gmina-koniusza/"
_AREAS = {
    "Muniaczkowice, Chorążyce, Dalewice, Rzędowice, Piotrkowice Wielkie, Budziejowice": r"^Muniaczkowice",
    "Niegardów, Niegardów Kolonia, Gnatowice, Przesławice, Zielona": r"^Niegardów",
    "Polekarcice, Łyszkowice, Biórków Wielki": r"^Polekarcice",
    "Koniusza, Piotrkowice Małe, Posądza": r"^Koniusza",
    "Wronin, Wroniec, Wąsów, Biórków Mały": r"^Wronin",
    "Górka Jaklińska, Karwin, Siedliska, Wierzbno": r"^Górka Jaklińska",
    "Czernichów, Glewiec, Glew, Szarbia": r"^Czernichów",
}
_TYPES = {
    "Zmieszane + Bio": [wt.GENERAL_WASTE, wt.ORGANIC],
    "Plastik + Papier": [wt.PLASTIC, wt.PAPER],
    "Szkło": wt.GLASS,
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Koniusza)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Koniusza."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Koniusza"),)
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PLASTIC,
        wt.PAPER,
        wt.GLASS,
    ]
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not an area"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Household calendar area"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Open Gmina Koniusza (mieszkańcy) at "
            "https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-koniusza/ and "
            "select the village group your village appears in. The current half-year "
            "calendar is found on the page each time, so a new upload is picked up "
            "without a change. Mixed and bio waste are collected on the same day, as are "
            "plastic and paper. Apartment blocks (zabudowa wielorodzinna) are only given "
            "as weekly and monthly rules without dates and are not supported."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _PAGE,
                pick=CalendarLink(
                    "Koniusza",
                    dict.fromkeys(_AREAS, "Harmonogram Koniusza"),
                    match_label=True,
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = RuledTableParser(min_cells=60, merged_cells=True)
    preprocess = MonthGrid(
        _TYPES, year_pattern=r"(20\d\d) R\.", areas=_AREAS, area_in="row"
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
