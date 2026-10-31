"""TAMAX household collection calendars for Gmina Miasto Bochnia."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfRuledTable import RuledTableParser
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.service.TamaxMonthGrid import MonthGrid
from waste_collection_schedule.transformers import ICSTransformer

_PAGE = f"{URL}/harmonogramy/malopolskie/gmina-bochnia/"
_ROUTES = {
    "I": "Bracka, Bernardyńska, Plac Czaplińskiego, Solna…",
    "II": "Brzozowa, Chodenicka, A. Furdzika, E. Karasia…",
    "III": "Kącik, Krakowska, Krakowskie Przedmieście, Oracka…",
    "IV": "Brzeska, Gen. H. Dąbrowskiego, Dołuszycka do obwodnicy, Rtm. W. Pileckiego…",
    "V": "Biała, kpt. J. Dubaniowskiego (Salwa), Kazimierza Wielkiego, Św. Marka…",
    "VI": "K. Brodzińskiego, Nowy Świat, W. Podgórca, Z. Włodka…",
    "VII": "Dębnik, Dołuszycka (od obwodnicy do granicy miasta), Dąbrówki, K. Frycza…",
    "VIII": "T. Czackiego, W. Gadowskiego, Górników, Kowalska…",
    "IX": "J.K. Andrusiewicza, G. Bukowskiego, Górska, Leśna…",
    "X": "Campi, M. Czyżewicza, E. Dembowskiego, Gipsowa…",
}
_AREAS = {
    f"Trasa {route}: {streets}": rf"TRASA {route}(?![IVX])"
    for route, streets in _ROUTES.items()
}
_TYPES = {
    "ZMIESZANE": wt.GENERAL_WASTE,
    "TWORZYWA SZTUCZNE": wt.PLASTIC,
    "PAPIER": wt.PAPER,
    "SZKŁO": wt.GLASS,
    "BIOODPADY": wt.ORGANIC,
    "POPIÓŁ": wt.OTHER,
    "TEKSTYLIA": wt.TEXTILES,
    "WIELKOGABARYTOWE": [wt.BULKY_WASTE, wt.ELECTRONICS],
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Miasto Bochnia)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Miasto Bochnia."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Miasto Bochnia"),)
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PLASTIC,
        wt.PAPER,
        wt.GLASS,
        wt.ORGANIC,
        wt.OTHER,
        wt.TEXTILES,
        wt.BULKY_WASTE,
        wt.ELECTRONICS,
    ]
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not a route"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Household calendar route"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Open Gmina Miasto Bochnia (mieszkańcy) at "
            "https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-bochnia/ and the "
            "JEDNORODZINNE (single-family housing) calendar, which has one page per route "
            "(TRASA). Select the route whose street list contains your street; the choices "
            "show the beginning of each list. Ash (POPIÓŁ) is reported as Other; the bulky "
            "waste collection also takes electrical equipment and tyres. Apartment blocks "
            "(WIELORODZINNE) are only given as weekday rules without dates and are not "
            "supported."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _PAGE,
                pick=CalendarLink(
                    "Miasto Bochnia",
                    dict.fromkeys(_AREAS, "JEDNORODZINNE"),
                    match_label=True,
                    require_year=False,
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = RuledTableParser(min_cells=300, merged_cells=True)
    preprocess = MonthGrid(
        _TYPES,
        year_pattern=r"Harmonogram odbioru odpadów (20\d\d)",
        areas=_AREAS,
        area_in="page",
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
