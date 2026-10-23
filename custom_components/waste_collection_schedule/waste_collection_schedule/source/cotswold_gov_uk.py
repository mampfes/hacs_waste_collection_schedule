import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.AuraWasteEnquiry import (
    AuraWasteEnquiryRetriever,
    AuraWasteTableParser,
)
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Refuse": wt.GENERAL_WASTE,
    "Black Recycling Box": wt.RECYCLABLES,
    "Blue Bag": wt.RECYCLABLES,
    "White Bag": wt.RECYCLABLES,
    "Garden Bin": wt.GARDEN_WASTE,
    "Outdoor Food Caddy": wt.FOOD_WASTE,
}


def _without_size(name: str) -> str:
    """``"180 Litre Refuse"`` -> ``"Refuse"``."""
    return re.sub(r"^\d+ Litre ", "", name.strip())


@final
class Source(BaseSource):
    TITLE = "Cotswold District Council"
    DESCRIPTION = "Source for Cotswold District Council, UK."
    URL = "https://www.cotswold.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    # Several recycling containers are collected together; the original label
    # stays in the description and the duplicates collapse by default.
    IGNORE_DUPLICATES_DEFAULT = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Parsons Piece, 1 Glebe Lane, Kemble, Cirencester": {
            "address": "PARSONS PIECE, 1 GLEBE LANE, KEMBLE, CIRENCESTER, GL7 6BD"
        },
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to the Cotswold District Council waste collection enquiry page "
            "(https://community.cotswold.gov.uk/s/waste-collection-enquiry) and "
            "start typing your postcode or street name into the address lookup. "
            "Select your property from the autocomplete suggestions and use the "
            "full address string exactly as it appears (e.g. "
            "'10 HAVEN HILL, CIRENCESTER, GL7 1BN')."
        ),
    }

    retrieve = AuraWasteEnquiryRetriever("community.cotswold.gov.uk", client_code="CDC")
    parse = AuraWasteTableParser()
    transform = RowTransformer(
        clean=_without_size, type_value_map=_TYPE_MAP, carry_raw_label=True
    )
