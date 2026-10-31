"""TAMAX household collection calendars for Miasto i Gmina Sędziszów."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfRuledTable import RuledTableParser
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.service.TamaxMonthGrid import MonthGrid
from waste_collection_schedule.transformers import ICSTransformer

_PAGE = f"{URL}/harmonogramy/swietokrzyskie/gmina-sedziszow/"
_AREAS = {
    "Sędziszów: Akacjowa, Batalionów Chłopskich, Bąkowska, Bohaterów Swaryszowa…": r"^SĘDZISZÓW ulice: Akacjowa",
    "Sędziszów: Armii Krajowej, Chabrowa, Dworcowa, Działkowa…": r"^SĘDZISZÓW ulice: Armii Krajowej",
    "Sosnowiec; Sędziszów: Brzozowa, Łąkowa, Marianów, Szałas, Tarnawa": r"^Sosnowiec",
    "Borszowice, Łowinia, Pawłowice, Pawłowice Zagaje, Wojciechowice": r"^Borszowice",
    "Białowieża, Bugaj, Czekaj Krzelów, Mstyczów, Swaryszów": r"^Białowieża",
    "Aleksandrów, Boleścice, Krzcięcice, Mierzyn, Piołunka, Słaboszowice": r"^Aleksandrów",
    "Gniewięcin, Klimontów, Klimontówek, Piła": r"^Gniewięcin",
    "Czepiec, Grązów, Jeżów, Przełaj, Przełaj Czepiecki, Podsadek, Zielonki": r"^Czepiec",
}
_TYPES = {
    "Odpady zmieszane": wt.GENERAL_WASTE,
    "BIO": wt.ORGANIC,
    "Plastik": wt.PLASTIC,
    "Papier": wt.PAPER,
    "Szkło": wt.GLASS,
    "Tekstylia": wt.TEXTILES,
    "Odpady wielkogabarytowe": wt.BULKY_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Sędziszów)"
    DESCRIPTION = (
        "Source for TAMAX household waste collection in Miasto i Gmina Sędziszów."
    )
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Sędziszów"),)
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PLASTIC,
        wt.PAPER,
        wt.GLASS,
        wt.TEXTILES,
        wt.BULKY_WASTE,
    ]
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not an area"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Household calendar area"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Open Gmina Sędziszów (mieszkańcy) at "
            "https://www.tamax.net.pl/harmonogramy/swietokrzyskie/gmina-sedziszow/ "
            "and the JEDNORODZINNE (single-family housing) calendar. Select the village "
            "group or street list your address appears in; street choices show the "
            "beginning of each list, read the PDF for the complete streets. The current "
            "half-year calendar is found on the page each time, so a new upload is picked "
            "up without a change. Apartment blocks, housing communities and businesses "
            "have separate calendars that are not supported."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _PAGE,
                pick=CalendarLink(
                    "Sędziszów",
                    dict.fromkeys(_AREAS, "JEDNORODZINNE"),
                    match_label=True,
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = RuledTableParser(min_cells=100, merged_cells=True)
    preprocess = MonthGrid(
        _TYPES, year_pattern=r"W (20\d\d) r\.", areas=_AREAS, area_in="row"
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
