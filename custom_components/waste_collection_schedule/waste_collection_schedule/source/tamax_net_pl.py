"""TAMAX household month-table calendars for Gmina Radziemice."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfTableParser
from waste_collection_schedule.preprocessors import PdfMonthRows
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.transformers import ICSTransformer

_PAGE = f"{URL}/harmonogramy/malopolskie/gmina-radziemice/"
_AREAS = {
    "Błogocice, Kąty, Kowary, Radziemice, Wola Gruszowska": "Radziemice-Wola-Gruszowska",
    "Dodów, Kaczowice, Lelowice, Przemęczanki, Smoniowice, Wrocimowice": "Dodow-Kaczowice",
    "Łętkowice, Obrażejowice, Wierzbica, Zielenice": "Letkowice-Obrazejowice",
}
_TYPES = {
    "komunalne": wt.GENERAL_WASTE,
    "segregowane": wt.RECYCLABLES,
    "biodegradowalne": wt.ORGANIC,
    "Popiół": wt.OTHER,
    "Wielkogabarytowe": [wt.BULKY_WASTE, wt.ELECTRONICS, wt.TEXTILES],
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Radziemice)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Radziemice."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Radziemice"),)

    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Village group"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "On https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-radziemice/ "
            "find Gmina Radziemice (mieszkańcy) and select the village group printed on your household calendar. "
            "Only these three Radziemice household tables are supported; other "
            "municipalities, apartment blocks and business calendars use different "
            "layouts. In particular, the Racławice download is for businesses. "
            "Ash (Popiół paleniskowy) is classified as Other and keeps its original "
            "label. The combined bulky collection also accepts electronics and "
            "textiles. Tyres have no separate canonical type."
        )
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_PAGE, pick=CalendarLink("Radziemice", _AREAS)),),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = PdfTableParser(min_words=40)
    preprocess = PdfMonthRows(labels=_TYPES, year_pattern=r"01\.01\.(20\d{2})")
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
