from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.service.LocalGovWasteCollection import (
    CollectionDaysParser,
    address_retriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Each day names every round collected in one sentence ("Recycling, garden
# waste and food waste collections"), so the parser splits it.


@final
class Source(BaseSource):
    TITLE = "Central Bedfordshire Council"
    DESCRIPTION = (
        "Source for www.centralbedfordshire.gov.uk services for Central Bedfordshire"
    )
    URL = "https://www.centralbedfordshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Buttermere Avenue, Dunstable": {
            "postcode": "LU6 3PD",
            "house_name": "1 Buttermere Avenue",
        },
        # The site accepts the postcode without its space too.
        "Chestnut Avenue, Biggleswade (unspaced postcode, separate garden waste row)": {
            "postcode": "SG180LL",
            "house_name": "1 Chestnut Avenue",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown house": {"postcode": "LU6 3PD", "house_name": "999 Nowhere"},
    }

    PARAMS = (
        postcode(),
        text_field("house_name", "House name or number (start of the address)"),
    )

    retrieve = address_retriever(
        "https://www.centralbedfordshire.gov.uk/waste-and-recycling/"
        "waste-collection-schedule",
        address="house_name",
    )
    parse = CollectionDaysParser(split=True)
    transform = RowTransformer(
        type_value_map={
            "Refuse (black bin)": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "garden waste": wt.GARDEN_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
            # A separate row for a garden-waste subscription, beside the
            # combined row naming the same round.
            "Garden waste collection (paid subscription)": wt.GARDEN_WASTE,
            "food waste": wt.FOOD_WASTE,
        },
    )
