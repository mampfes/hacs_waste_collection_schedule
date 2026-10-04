from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    postcode,
    street_address,
    uprn,
)
from waste_collection_schedule.service.DrupalWasteForm import (
    WasteCardsParser,
    WasteFormRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day"


@final
class Source(BaseSource):
    TITLE = "Wokingham Borough Council"
    DESCRIPTION = "Source for wokingham.gov.uk services for Wokingham, UK."
    URL = "https://wokingham.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "RG40 1GE", "property": "10032935729"},
        "Test_002": {"postcode": "RG413BP", "property": "14007633"},
        "Test_003": {"postcode": "rg41 1ph", "property": 14040037},
        "Test_004": {"postcode": "RG40 2LW", "address": "16 Davy Close"},
        "No-Collection Test": {"postcode": "RG10 0EU", "address": "39 Broadwater Road"},
    }

    PARAMS = (
        postcode(),
        alternatives([uprn("property")], [street_address()]),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode together with either the first line of your "
            "address (e.g. '16 Davy Close'; the first address on the council's "
            "list that contains it is used) or the property number, which is the "
            "UPRN. To find it, open "
            "https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day, "
            "look up your postcode and read the value of your address's "
            "<option> in the page source, e.g. 10032935729 for "
            "'32, SAMBORNE DRIVE, WOKINGHAM'."
        ),
    }

    retrieve = WasteFormRetriever(API_URL)
    parse = WasteCardsParser()
    transform = RowTransformer(
        type_value_map={
            "Household waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden waste": wt.GARDEN_WASTE,
            "Food waste": wt.FOOD_WASTE,
        },
    )
