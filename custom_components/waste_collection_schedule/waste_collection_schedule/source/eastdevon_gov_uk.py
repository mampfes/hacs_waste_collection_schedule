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
    TITLE = "East Devon District Council"
    DESCRIPTION = "Source for East Devon services for East Devon District Council, UK."
    URL = "https://eastdevon.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@SimonRice"]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "010000246114"},
        "Test_002": {"uprn": 10000272679},
        "Test_003": {"postcode": "EX8 2AN", "address": "1 Dagmar Road"},
        "Test_004": {"postcode": "EX5 2AB", "address": "1 Blackhorse Cottages"},
    }

    PARAMS = (
        alternatives([uprn()], [postcode()]),
        street_address(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or your postcode plus an address to match. "
            "Find your UPRN at https://www.findmyaddress.co.uk/, or from the "
            "UPRN query parameter on the East Devon bin collection page."
        ),
    }

    retrieve = Cloud9Retriever(
        "eastdevon",
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
            "Refuse Bins": wt.GENERAL_WASTE,
            "Recycling Box and Sack": wt.RECYCLABLES,
            "Food Caddies": wt.FOOD_WASTE,
            "Green Waste Bins": wt.GARDEN_WASTE,
        },
    )

    def __init__(
        self,
        uprn: "str | int | None" = None,
        postcode: str | None = None,
        address: str | None = None,
    ):
        # Existing configurations pass a bare UPRN, which this council's UPRN
        # scheme wants zero-padded to 12 digits; keep the padding so they
        # keep working (carried over from the pre-Cloud9 source).
        super().__init__(
            uprn=str(uprn).zfill(12) if uprn else None,
            postcode=postcode,
            address=address,
        )
