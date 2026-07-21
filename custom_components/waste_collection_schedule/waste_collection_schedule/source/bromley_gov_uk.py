"""London Borough of Bromley (bromley.gov.uk).

Demonstrates: the UK htmx polling shape (same shell as bexley_gov_uk). The
property page kicks off server-side calendar generation; the site's own page
polls the ``.ics`` endpoint every 2 seconds (``hx-trigger="every 2s"``) until
it's ready. ``PollingIcsRetriever`` mirrors that polling; ``IcsParser`` +
``ICSTransformer`` do the rest. The only source-specific code is the URL
template, a " collection" suffix strip (every summary ends with it, e.g.
"Food Waste collection"), and the waste-type map.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import PollingIcsRetriever
from waste_collection_schedule.transformers import ICSTransformer, label_cleaner
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    PAPER,
)


@final
class Source(BaseSource):
    TITLE = "London Borough of Bromley"
    DESCRIPTION = (
        "Source for bromley.gov.uk services for London Borough of Bromley, UK."
    )
    URL = "https://bromley.gov.uk"
    COUNTRY = "uk"

    # UPRN/property-id lookup: a wrong id yields no collections, so surface
    # it as an error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"property": 6328436},
        "Test_002": {"property": "6146611"},
        "Test_003": {"property": 6283460},
    }

    PARAMS = (uprn(field_name="property"),)

    retrieve = PollingIcsRetriever(
        url=lambda property, **_: (
            f"https://recyclingservices.bromley.gov.uk/waste/{property}"
        )
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Non-Recyclable Refuse": GENERAL_WASTE,
            "Food Waste": FOOD_WASTE,
            "Garden Waste": GARDEN_WASTE,
            "Paper & Cardboard": PAPER,
            "Mixed Recycling (Cans, Plastics & Glass)": GLASS,
        },
        clean=label_cleaner(strip_suffixes=[" collection"]),
    )

    def __init__(self, property: str):
        super().__init__(property=property)
