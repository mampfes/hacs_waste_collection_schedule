"""Redbridge Council, London, UK.

Demonstrates: the plainest text-PDF path. The council generates a per-property
calendar PDF (keyed by UPRN) whose text layer is a month-by-month grid, so a
plain ``PdfTextParser`` returns the whole text and ``TextCalendarGrid`` walks
it into ``(date, service)`` records. ``ICSTransformer`` maps the four service
names onto canonical WasteTypes. No layout mode, no coordinates: when a text
PDF reads cleanly, this is all a source needs.
"""

from typing import ClassVar, final

from waste_collection_schedule import config_params
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.preprocessors import TextCalendarGrid
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://my.redbridge.gov.uk/RecycleRefuse/GetFile"

# The service names the PDF prints, keyed by their leading word.
_TYPE_MAP = {
    "REFUSE": wt.GENERAL_WASTE,
    "RECYCLING": wt.RECYCLABLES,
    "GARDEN": wt.GARDEN_WASTE,
    "FOOD": wt.FOOD_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Redbridge Council"
    DESCRIPTION = "Source for redbridge.gov.uk services for Redbridge Council, UK."
    URL = "https://redbridge.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "council office recycling only": {"uprn": 10034922090},
        "refuse and recycling only": {"uprn": 10013585215},
        "a church vicarage, garden, recycling, refuse": {"uprn": 10034912354},
    }

    PARAMS = (config_params.uprn(),)

    retrieve = HttpGetRetriever(url=_API_URL, params=lambda uprn: {"uprn": uprn})
    parse = PdfTextParser(min_chars=100)
    # The grid's own furniture (month heading, weekday header, day rows) is the
    # component's job; all this council adds is the section title printed
    # between the months, which also ends a day's list of services.
    preprocess = TextCalendarGrid(
        keys=_TYPE_MAP,
        stop_contains=("your collection schedule",),
    )

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
