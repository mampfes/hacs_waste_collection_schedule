from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.service.LocalGovWasteCollection import (
    CollectionDaysParser,
    uprn_retriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Wirral Council"
    DESCRIPTION = "Source for wirral.gov.uk services for Wirral Council, UK."
    URL = "https://wirral.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Elm Avenue, Upton": {
            "postcode": "CH49 4NP",
            "address_value": "000042037487",
        },
        "Vernon Avenue, Seacombe (with food waste)": {
            "postcode": "CH44 7ES",
            "address_value": "42119794",
        },
    }

    # The postcode is no longer needed; it stays optional so existing
    # configurations keep working.
    PARAMS = (
        text_field("address_value", "Address value (UPRN)"),
        text_field("postcode", term=POSTCODE, optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates, "
            "enter your postcode and select your address. The number at the end of "
            "the resulting web address (.../view/42119794) is your address value."
        ),
    }

    retrieve = uprn_retriever(
        "https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates",
        "address_value",
        # Older values were zero-padded to twelve digits; the site wants the
        # plain UPRN.
        normalise=lambda value: value.lstrip("0"),
    )
    parse = CollectionDaysParser()
    transform = RowTransformer(
        type_value_map={
            "Green non-recyclable": wt.GENERAL_WASTE,
            "Grey recycling": wt.RECYCLABLES,
            "Grey food waste": wt.FOOD_WASTE,
            "Brown garden waste": wt.GARDEN_WASTE,
        },
    )
