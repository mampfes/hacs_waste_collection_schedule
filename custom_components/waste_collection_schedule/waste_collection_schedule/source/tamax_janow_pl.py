"""TAMAX household collection calendars for Gmina Janów."""

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
    "Janów": "-Janow.pdf",
    "Apolonka, Bystrzanowice, Bystrzanowice Dwór, Góry Gorzkowskie, Hucisko, Lgoczanka, Sokole Pole, Teodorów": "Apolonka-Bystrzanowice",
    "Czepurka, Pabianice, Siedlec, Skowronów": "Pabianice-Siedlec-Skowronow-Czepurka",
    "Piasek, Ponik, Zagórze, Śmiertny Dąb": "Piasek-Ponik-Zagorze-Smiertny-Dab",
    "Lusławice, Lipnik, Okrąglik, Żuraw": "Luslawice-Lipnik-Okraglik-Zuraw",
    "Trudne wjazdy": "-TRUDNE-WJAZDY.pdf",
}
_TYPES = {
    "komunalne": wt.GENERAL_WASTE,
    "segregowane": wt.RECYCLABLES,
    "biodegradowalne": wt.ORGANIC,
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Janów)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Janów."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Janów"),)
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not a route"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Household calendar area"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Find Gmina Janów (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/. "
            "Select your village group exactly as printed on the household PDF. "
            "Use Trudne wjazdy only if the council has assigned your property to that route. "
            "Apartment-block and business schedules are not supported. Mixed recycling "
            "includes the plastic/metal, paper and glass bags collected together. "
            "M-PSZOK collections require registration and have no dated appointments in this calendar."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{URL}/harmonogramy/", pick=CalendarLink("Janów", _AREAS)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = PdfTableParser(min_words=40)
    preprocess = DatedColumns(_TYPES)
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
