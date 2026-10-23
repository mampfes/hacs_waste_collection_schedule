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
    "Recycling": wt.RECYCLABLES,
    "Garden Bin": wt.GARDEN_WASTE,
    "Outdoor Food Caddy": wt.FOOD_WASTE,
}


def _without_size(name: str) -> str:
    """``"180 Litre Refuse"`` -> ``"Refuse"``."""
    return re.sub(r"^\d+ Litre ", "", name.strip())


@final
class Source(BaseSource):
    TITLE = "West Oxfordshire District Council"
    DESCRIPTION = "Source for West Oxfordshire District Council."
    URL = "https://westoxon.gov.uk/"
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
        "75 manor road woodstock, ox20 1xr": {
            "address": "75 manor road woodstock, ox20 1xr"
        },
        "test": {"address": "65 MAIN ROAD, LONG HANBOROUGH, WITNEY, OX29 8JX"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to the West Oxfordshire waste collection enquiry page "
            "(https://community.westoxon.gov.uk/s/waste-collection-enquiry) and "
            "type your postcode or street name into the address lookup. Use the "
            "full address string exactly as it is returned by the autocomplete."
        ),
    }

    retrieve = AuraWasteEnquiryRetriever("community.westoxon.gov.uk", client_code="WOD")
    parse = AuraWasteTableParser()
    transform = RowTransformer(
        clean=_without_size, type_value_map=_TYPE_MAP, carry_raw_label=True
    )
