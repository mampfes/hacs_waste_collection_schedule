"""Sutton Council, London (sutton.gov.uk).

Demonstrates: the same "recyclingservices" council-platform shape as
bexley_gov_uk/bromley_gov_uk (the legacy source polled the property page's
``hx-get`` attribute directly rather than the ``.ics`` endpoint's body, but
``PollingIcsRetriever``'s default calendar-endpoint poll reaches the same
ready state). ``PollingIcsRetriever`` + ``IcsParser`` + ``ICSTransformer`` do
all the work; this module only supplies the URL template, a " collection"
suffix strip, and the waste-type map (Sutton icons "mixed" recycling as
plain Recycling, unlike Bromley's Glass).
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import PollingIcsRetriever
from waste_collection_schedule.transformers import ICSTransformer, label_cleaner
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GENERAL_WASTE,
    PAPER,
    RECYCLABLES,
)


@final
class Source(BaseSource):
    TITLE = "Sutton Council, London"
    DESCRIPTION = "Source for Sutton Council, London."
    URL = "https://sutton.gov.uk"
    COUNTRY = "uk"

    # UPRN/property-id lookup: a wrong id yields no collections, so surface
    # it as an error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "4721996": {"id": 4721996},
        "4499298": {"id": "4499298"},
    }

    PARAMS = (uprn(field_name="id"),)

    retrieve = PollingIcsRetriever(
        url=lambda id, **_: f"https://waste-services.sutton.gov.uk/waste/{id}"
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Non-Recyclable Refuse": GENERAL_WASTE,
            "Food Waste": FOOD_WASTE,
            "Paper & Card": PAPER,
            "Mixed Recycling (Cans, Plastics & Glass)": RECYCLABLES,
        },
        clean=label_cleaner(strip_suffixes=[" collection"]),
    )

    def __init__(self, id: str | int):
        super().__init__(id=id)
