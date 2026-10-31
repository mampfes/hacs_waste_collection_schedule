"""TAMAX household collection calendars for Gmina Lelów."""

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
    "Lelów (bez ul. Spacerowej), Lgota Błotna, Lgota Gawronna": "Lelow-bez-ulkicy-Spacerowej",
    "Lelów (ul. Spacerowa), Nakło, Paulinów, Turzyn, Ślęzany": "Naklo-Paulinow-Turzyn",
    "Biała Błotna, Drochlin": "Biala-Blotna-Drochlin",
    "Celiny, Konstantynów, Mełchów, Podlesie, Skrajniwa, Staromieście": "Celiny-Konstantynow-Melchow",
    "Trudne wjazdy": "-Trudne-wjazdy.pdf",
}
_TYPES = {
    "Zmieszane": wt.GENERAL_WASTE,
    "Segregowane": wt.RECYCLABLES,
    "Bio": wt.ORGANIC,
    "Popiół": wt.OTHER,
    "Wielkogabarytowe": [wt.BULKY_WASTE, wt.ELECTRONICS],
}


@final
class Source(BaseSource):
    TITLE = "TAMAX (Gmina Lelów)"
    DESCRIPTION = "Source for TAMAX household waste collection in Gmina Lelów."
    URL = URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    REGIONS = (region("Gmina Lelów"),)
    TEST_CASES: ClassVar[dict] = {name: {"area": name} for name in _AREAS}
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown area": {"area": "not a route"}}
    PARAMS = (config_params.dropdown("area", list(_AREAS), "Household calendar area"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Find Gmina Lelów (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/. "
            "Select the exact household village group; Lelów's Spacerowa street has a separate route. "
            "Use Trudne wjazdy only if the council assigned your property to that route. "
            "Yellow cells collect mixed waste and bio; red cells collect mixed waste and recycling; "
            "brown cells collect ash, classified as Other with the original Popiół label. "
            "The dated bulky notice includes furniture and complete electrical equipment. "
            "Tyres and construction items have no separate canonical type. Apartment-block and business calendars are not supported."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{URL}/harmonogramy/", pick=CalendarLink("Lelów", _AREAS)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = HouseholdCalendarParser(separate_ash=True)
    transform = JsonTransformer(
        date_key="date", type_key="type", type_value_map=_TYPES, carry_raw_label=True
    )
