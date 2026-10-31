"""TAMAX household collection calendars for Gmina Imielno."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfTableParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.ImielnoCalendar import VillageDateRows
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.transformers import ICSTransformer

_AREAS = dict.fromkeys(
    [
        "Borszowice",
        "Motkowice",
        "Wygoda",
        "Bełk",
        "Grudzyny",
        "Kawęczyn",
        "Mierzwin",
        "Opatkowice Cysterskie",
        "Opatkowice Drewniane",
        "Opatkowice Murowane",
        "Opatkowice Pojałowskie",
        "Zegartowice",
        "Dalechowy",
        "Dzierszyn",
        "Helenówka",
        "Jakubów",
        "Karczunek",
        "Rajchotka",
        "Imielno",
        "Imielnica",
        "Sobowice",
        "Stawy",
    ],
    "Harmonogram-Imielno.pdf",
)
_TYPES = {
    "Zmieszane i bio": [wt.GENERAL_WASTE, wt.ORGANIC],
    "Segregowane": wt.RECYCLABLES,
    "Wielkogabarytowe": [wt.BULKY_WASTE, wt.ELECTRONICS],
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Imielno)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Imielno."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Imielno"),)
    TEST_CASES: ClassVar[dict] = {
        name: {"area": name}
        for name in ("Imielno", "Borszowice", "Opatkowice Murowane", "Karczunek")
    }
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not a route"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Village"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Find Gmina Imielno (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/ and select your village. "
            "The source reads the printed day-and-Roman-month dates, including holiday exceptions. "
            "Mixed waste/bio and recycling use different village groups and are matched independently. "
            "The four dated bulky collections also accept complete electrical equipment. "
            "Tyres have no separate canonical type. Business calendars are not supported."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{URL}/harmonogramy/", pick=CalendarLink("Imielno", _AREAS)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = PdfTableParser(min_words=30)
    preprocess = VillageDateRows()
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
