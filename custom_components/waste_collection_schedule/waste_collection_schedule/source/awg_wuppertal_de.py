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

A handful of streets fall into more than one collection area (district
boundaries running through them); AWG then shows a house-number picker
instead of a calendar, which is why ``house_number`` exists (see #7368). Most
streets never hit it, so it is optional; ``WasteCalendarRetriever`` only
consults it once the street alone resolves to no feeds.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.BwWasteCalendar import WasteCalendarRetriever
from waste_collection_schedule.transformers import ICSTransformer

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

    TEST_CASES: ClassVar[dict] = {
        "Hauptstraße": {"street": "Hauptstraße"},
        "Nützenberger Straße 1": {
            "street": "Nützenberger Straße",
            "house_number": "1",
        },
    }

    PARAMS = (street(field="street"), house_number(optional=True))

    retrieve = WasteCalendarRetriever(
        url=_API_URL, base_url=_BASE_URL, house_number_argument="house_number"
    )
    parse = parsers.EachResponse(
        parsers.IcsParser(split_at="/", regex=r"(.*)/ !!! Terminverschiebung !!!")
    )

    transform = ICSTransformer(
        clean=_leading_type,
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Gelb": wt.RECYCLABLES,
            "Bio": wt.ORGANIC,
            "Papier": wt.PAPER,
            "Sperrmüll": wt.BULKY_WASTE,
        },
    )
