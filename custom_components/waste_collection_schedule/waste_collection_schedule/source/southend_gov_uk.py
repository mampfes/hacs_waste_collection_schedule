from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    postcode,
    street_address,
    uprn,
)
from waste_collection_schedule.service.uk_cloud9_apps import (
    Cloud9Parser,
    Cloud9Retriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    PAPER,
    RECYCLABLES,
)


@final
class Source(BaseSource):
    TITLE = "Southend-on-Sea City Council"
    DESCRIPTION = (
        "Source for southend.gov.uk services for Southend-on-Sea City Council, UK."
    )
    URL = "https://www.southend.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 100090691871},
        "Test_002": {"uprn": "100090700485"},
        "Test_003": {
            "postcode": "SS3 9JD",
            "address": "38 Thorpedene Gardens, Shoeburyness",
        },
    }

    PARAMS = (
        alternatives([uprn()], [postcode()]),
        street_address(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or your postcode plus an address to match. "
            "Find your UPRN at https://www.findmyaddress.co.uk/ by entering "
            "your address details."
        ),
    }

    retrieve = Cloud9Retriever(
        "southend",
        uprn_field="uprn",
        postcode_field="postcode",
        address_field="address",
        argument_name="postcode",
    )
    parse = Cloud9Parser()
    # Southend collects mixed recycling (plastic, glass, cans) in the pink lid
    # bin and paper and card in the blue lid bin.
    transform = RowTransformer(
        type_value_map={
            "Refuse Bin": GENERAL_WASTE,
            "Pink Lid Recycling Bin": RECYCLABLES,
            "Blue Lid Recycling Bin": PAPER,
            "Food Caddy": FOOD_WASTE,
            "Garden Waste": GARDEN_WASTE,
        },
    )
