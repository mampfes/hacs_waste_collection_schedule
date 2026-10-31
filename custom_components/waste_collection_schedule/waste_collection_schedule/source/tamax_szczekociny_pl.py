"""TAMAX household collection calendars for Gmina Szczekociny."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfTableParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.DatedPdfColumns import DatedColumns
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.transformers import ICSTransformer

_AREAS = {
    "Szczekociny: 8 Pułku Ułanów, Boczna, Centralna, Dębowa…": "Szczekociny-ulice-8-Pulku-Ulanow",
    "Szczekociny: Akacjowa, Brzozowa, Głowackiego, Grochowskiego, Jana Pawła II…": "Szczekociny-ulice-Akacjowa",
    "Szczekociny: Al. Zwycięstwa, Cmentarna, ks. Ściegiennego, Lelowska…": "Szczekociny-ulice-Al.-Zwyciestwa",
    "Rokitno, Ołudza, Wólka Ołudzka, Grabiec": "Rokitno-Oludza-Wolka-Oludzka-Grabiec",
    "Goleniowy, Chałupki, Bógdał, Drużykowa, Rędziny, Starzyny, Wólka Starzyńska": "Goleniowy-Chalupki-Bogdal",
    "Przyłęk, Szyszki, Brzostek, Tęgobórz, Gustawów-Małachów, Siedliska, Bonowice": "Przylek-SzyszkiBrzostek",
    "Trudne wjazdy oraz domki letniskowe": "trasa-trudne-wjazdy-oraz-domki-letniskowe",
}
_TYPES = {
    "komunalne": wt.GENERAL_WASTE,
    "segregowane": wt.RECYCLABLES,
    "biodegradowalne": wt.ORGANIC,
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Szczekociny)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Szczekociny."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Szczekociny"),)
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not a route"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Household calendar area"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Find Gmina Szczekociny (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/. "
            "Select your village group or street list exactly as printed on the household PDF. Street choices show the beginning of each list; read its PDF for the complete streets. "
            "Use the Trudne wjazdy / domki letniskowe route only if the council has assigned your property to that route. "
            "Apartment-block and business schedules are not supported. Mixed recycling "
            "includes the plastic/metal, paper and glass bags collected together. "
            "Textiles and bulky items go to the collection centre; no undated drop-off or appointment is added."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{URL}/harmonogramy/", pick=CalendarLink("Szczekociny", _AREAS)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = PdfTableParser(min_words=40)
    preprocess = DatedColumns(_TYPES)
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
