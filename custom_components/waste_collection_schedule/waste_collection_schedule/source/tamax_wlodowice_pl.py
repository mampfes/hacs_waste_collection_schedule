"""TAMAX household collection calendars for Gmina Włodowice."""

from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.Tamax import URL, CalendarLink
from waste_collection_schedule.service.TamaxMarkedCalendar import (
    HouseholdCalendarParser,
)
from waste_collection_schedule.transformers import JsonTransformer

_AREAS = {
    "Włodowice (bez ul. Kopaniny, Różana i Leszczynowa), Morsko": "Wlodowice-Morsko",
    "Rudniki (bez ul. Górniczej), Włodowice (ul. Kopaniny i Różana)": "Rudniki-bez-ulicy-Gorniczej",
    "Rudniki (ul. Górnicza), Parkoszowice, Skałka, Włodowice (ul. Leszczynowa)": "Rudniki-ul.-Gornicza",
    "Rzędkowice, Góra Włodowska": "Rzedkowice-Gora-Wlodowska",
    "Zdów, Hucisko": "Zdow-Hucisko",
    "Trudne wjazdy": "-trasa-trudne-wjazdy.pdf",
}
_TYPES = {
    "Zmieszane": wt.GENERAL_WASTE,
    "Segregowane": wt.RECYCLABLES,
    "Bio": wt.ORGANIC,
    "Popiół": wt.OTHER,
    "Wielkogabarytowe": wt.BULKY_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Włodowice)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Włodowice."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Włodowice"),)
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not a route"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Household calendar area"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Find Gmina Włodowice (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/. "
            "Select your exact village group, including the street exceptions in Włodowice and Rudniki. "
            "Use Trudne wjazdy only if the council assigned your property to that route. "
            "Yellow cells collect mixed waste and bio. Red cells collect mixed waste and all listed "
            "segregated fractions, including recycling, bio and ash. Ash is Other with the original Popiół label. "
            "The dated bulky collection is also read from the PDF, even though it is operated separately by "
            "Przedsiębiorstwo Komunalne Ogrodzieniec. Collection-centre opening days (PSZOK), "
            "apartment-block and business schedules are not household collection events."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{URL}/harmonogramy/", pick=CalendarLink("Włodowice", _AREAS)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = HouseholdCalendarParser(separate_ash=False)
    transform = JsonTransformer(
        date_key="date", type_key="type", type_value_map=_TYPES, carry_raw_label=True
    )
