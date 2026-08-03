"""AWG Wuppertal (awg-wuppertal.de).

Composes: :class:`~waste_collection_schedule.service.BwWasteCalendar.WasteCalendarRetriever`
(the council runs the ``bw_wastecalendar`` TYPO3 plugin: autocomplete the
street, replay the plugin's form, then download the per-waste-type "als iCal"
feeds it lists) with
:class:`~waste_collection_schedule.parsers.EachResponse` around a plain
``IcsParser``. Nothing about that flow is Wuppertal's, so it lives in the
platform module and the source declares only its URLs.

The feeds title a postponed collection "<type> / !!! Terminverschiebung !!!"
and occasionally suffix the type itself; ``regex`` trims the first and the
transformer's ``clean`` the second.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.service.BwWasteCalendar import WasteCalendarRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://awg-wuppertal.de"
_API_URL = f"{_BASE_URL}/privatkunden/abfallkalender.html"


def _leading_type(label: str) -> str:
    """The bin name alone: the feeds suffix some titles with " - <detail>"."""
    return label.split("-")[0].strip()


@final
class Source(BaseSource):
    TITLE = "AWG Wuppertal"
    DESCRIPTION = "Source for AWG Wuppertal."
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {"Hauptstraße": {"street": "Hauptstraße"}}

    PARAMS = (street(field="street"),)

    retrieve = WasteCalendarRetriever(url=_API_URL, base_url=_BASE_URL)
    parse = parsers.EachResponse(
        parsers.IcsParser(split_at="/", regex=r"(.*)/ !!! Terminverschiebung !!!")
    )

    transform = ICSTransformer(
        clean=_leading_type,
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Gelb": RECYCLABLES,
            "Bio": ORGANIC,
            "Papier": PAPER,
            "Sperrmüll": BULKY_WASTE,
        },
    )
