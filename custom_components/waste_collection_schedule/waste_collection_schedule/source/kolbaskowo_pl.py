"""Gmina Kołbaskowo, Poland.

Single-family schedules (zabudowa jednorodzinna) are one PDF per village,
linked from a stable index page. Some villages are split: Kurów excludes
ul. Na Klifie and ul. Wichrowe Wzgórza from the main file, Będargowo and
Siadło Dolne split on house numbers, Stobno 52-54 is "Małe Stobno". The
optional street and house number pick that file; without them the file that
covers the rest of the village is used.

The PDF is a month-column table. Plastik, Papier and Szkło share one merged
cell, so those three rounds fall on the same days. Reading the borders and
the days lives in ``service/KolbaskowoSchedule.py``. Multi-family housing
(wspólnoty i spółdzielnie) is a separate page and is not read here.
"""

from typing import Any, ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, house_number, street
from waste_collection_schedule.service.KolbaskowoSchedule import (
    ScheduleParser,
    choose_schedule,
    schedule_links,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://kolbaskowo.pl/harmonogramy-odbioru-odpadow-dla-zabudowy-jednorodzinnej.html"
_HEADERS = {"Accept-Language": "pl,en;q=0.8"}

_TYPES = {
    "Zmieszane": wt.GENERAL_WASTE,
    # Plastik and metal are collected together.
    "Plastik, metal": wt.RECYCLABLES,
    "Papier": wt.PAPER,
    "Szkło": wt.GLASS,
    "BIO": wt.ORGANIC,
    "Gabaryty": wt.BULKY_WASTE,
}


def _schedule_url(
    response: Any,
    *_keys: Any,
    district: str,
    street: str | None = None,
    house_number: str | None = None,
    **_: Any,
) -> str:
    """The index page's PDF for this village, street or house number."""
    return choose_schedule(
        schedule_links(response),
        district,
        street=street,
        house_number=house_number,
    )


@final
class Source(BaseSource):
    TITLE = "Gmina Kołbaskowo"
    DESCRIPTION = "Source for Gmina Kołbaskowo, Poland (single-family housing)."
    URL = "https://kolbaskowo.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.ORGANIC,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        # Kurów 1: the main file, not ul. Na Klifie or ul. Wichrowe Wzgórza.
        "Kurow": {"district": "Kurów"},
        "Kurow, Na Klifie": {"district": "Kurów", "street": "Na Klifie"},
        "Bedargowo 52": {"district": "Będargowo", "house_number": "52"},
    }

    PARAMS = (
        district("district"),
        street("street", optional=True),
        house_number("house_number", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your village as named on "
            "https://kolbaskowo.pl/harmonogramy-odbioru-odpadow-dla-zabudowy-jednorodzinnej.html "
            "(e.g. 'Kurów' or 'Kołbaskowo'). 'Kurów' is the schedule for the "
            "village except ul. Na Klifie and ul. Wichrowe Wzgórza; set street "
            "to one of those (e.g. 'Na Klifie') for their file. For Będargowo "
            "50-57, Siadło Dolne 32, 32a or 34-63, or Stobno 52-54 (Małe Stobno), "
            "also enter the house number. You can instead paste the full link "
            "title. This covers single-family housing only."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_INDEX_URL, pick=_schedule_url, headers=_HEADERS),),
        url=lambda pdf, **_: pdf,
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = ScheduleParser()
    transform = ICSTransformer(type_value_map=_TYPES)
