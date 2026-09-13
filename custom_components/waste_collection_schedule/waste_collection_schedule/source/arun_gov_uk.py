from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
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


@final
class Source(BaseSource):
    TITLE = "Arun District Council"
    DESCRIPTION = "Source for arun.gov.uk services for Arun District, UK."
    URL = "https://www.arun.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {
            "postcode": "BN17 5JA",
            "address": "21A Beach Road, Littlehampton",
        },
        "Test_002": {"postcode": "BN16 1AA", "address": "2 Downs Way, East Preston"},
        "Test_003": {"uprn": 100062180214},
        "Test_004": {"uprn": "0100062180214"},
    }

    PARAMS = (
        alternatives([uprn()], [postcode()]),
        street_address(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or your postcode plus an address to match. "
            "Find your UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    retrieve = Cloud9Retriever(
        "arun",
        uprn_field="uprn",
        postcode_field="postcode",
        address_field="address",
        # The client's suggestions are whole address strings and it reports
        # the address it was given as the offending value, so they belong to
        # the address argument: picking one has to refine `address`, not
        # overwrite the postcode with a full address.
        argument_name="address",
    )
    parse = Cloud9Parser()
    transform = RowTransformer(
        type_value_map={
            "General Waste Bins": wt.GENERAL_WASTE,
            "Recycling Bins": wt.RECYCLABLES,
            "Food Waste Bins": wt.FOOD_WASTE,
            "Garden Waste Bins": wt.GARDEN_WASTE,
        },
    )
