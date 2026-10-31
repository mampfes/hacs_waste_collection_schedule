"""TAMAX household collection calendars for Miasto Wieliczka."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfRuledTable import RuledTableParser
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.service.TamaxMonthGrid import MonthGrid
from waste_collection_schedule.transformers import ICSTransformer

_PAGE = f"{URL}/harmonogramy/malopolskie/gmina-wieliczka/"
_AREAS = {
    "Rejon I: Bednarka, Czarnochowska, Daniłowicza, Deskura…": "REJON I Bednarka",
    "Rejon II: Asnyka, Bogucka, Dębowa, Kilińskiego…": "REJON II Asnyka",
    "Rejon III: Boża Wola, Chopina, Dembowskiego, Głowackiego…": "REJON III Boża Wola",
    "Rejon IV: Batorego, Graniczna, Krakowska, Krakowska Boczna…": "REJON IV Batorego",
    "Rejon V: Chabrowa, Gdowska, Jagielskiego, Jedynaka…": "REJON V Chabrowa",
    "Rejon VI: Armii Krajowej, Czubinów, Goliana, Górska…": "REJON VI Armii Krajowej",
    "Rejon VII: Akacjowa, Bajeczna, Św. Barbary, Jagiełły…": "REJON VII Akacjowa",
    "Rejon VIII: Aywasa, Bat. Chłopskich, Bukowa, Brodzińskiego…": "REJON VIII Aywasa",
}
_TYPES = {
    "ZMIESZANE": wt.GENERAL_WASTE,
    "BIO - odpady": wt.ORGANIC,
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Miasto Wieliczka)"
    DESCRIPTION = (
        "Source for TAMAX household mixed and bio waste collection in Miasto Wieliczka."
    )
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Miasto Wieliczka"),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC]
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not a district"}}
    PARAMS = (
        config_params.dropdown("area", list(_AREAS), "Household calendar district"),
    )
    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-wieliczka/ and "
            "select the district (REJON) whose PDF lists your street; the choices show the "
            "beginning of each street list. These district calendars list only the mixed "
            "and bio waste dates; other fractions are not printed in them and are not "
            "included."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _PAGE,
                pick=CalendarLink("Wieliczka", _AREAS, match_label=True),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = RuledTableParser(min_cells=30, merged_cells=True)
    preprocess = MonthGrid(_TYPES, year_pattern=r"Harmonogram odbioru odpadów (20\d\d)")
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
