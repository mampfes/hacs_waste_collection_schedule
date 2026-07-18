from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    postcode,
    street,
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
    TITLE = "North Herts Council"
    DESCRIPTION = "Source for www.north-herts.gov.uk services for North Herts Council."
    URL = "https://www.north-herts.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Example": {
            "address_postcode": "SG4 9QY",
            "address_name_numer": "26",
            "address_street": "BENSLOW RISE",
        },
        "Example No Postcode Space": {
            "address_postcode": "SG49QY",
            "address_name_numer": "26",
            "address_street": "BENSLOW RISE",
        },
        "Example fuzzy matching": {
            "address_postcode": "SG6 4EG",
            "address_name_numer": "4",
            "address_street": "Wilbury Road",
        },
        "Example garden waste": {
            "address_postcode": "SG8 5BN",
            "address_name_numer": "37",
            "address_street": "Heathfield",
        },
    }

    # The ``address_name_numer`` wire name (a typo for "number") is preserved
    # from the original source so existing user configurations keep working.
    PARAMS = (
        postcode(postcode_field="address_postcode"),
        house_number(field="address_name_numer", optional=True),
        street(field="address_street", optional=True),
        city(field="street_town", optional=True),
    )

    retrieve = Cloud9Retriever(
        "northherts",
        postcode_field="address_postcode",
        name_number_field="address_name_numer",
        street_field="address_street",
        town_field="street_town",
        argument_name="address_postcode",
    )
    parse = Cloud9Parser()
    transform = RowTransformer(
        type_value_map={
            "Non-recyclable refuse bin": GENERAL_WASTE,
            "Mixed recycling bin": RECYCLABLES,
            "Cardboard & paper bin": PAPER,
            "Food Caddy": FOOD_WASTE,
            "Garden waste bin": GARDEN_WASTE,
        },
    )

    def __init__(
        self,
        address_name_numer=None,
        address_street=None,
        street_town=None,
        address_postcode=None,
    ):
        super().__init__(
            address_name_numer=address_name_numer,
            address_street=address_street,
            street_town=street_town,
            address_postcode=address_postcode,
        )
