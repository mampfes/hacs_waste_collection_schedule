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
    "Green Recycling Box": wt.RECYCLABLES,
    "Blue Bag": wt.RECYCLABLES,
    "Garden Bin": wt.GARDEN_WASTE,
    "Outdoor Food Caddy": wt.FOOD_WASTE,
}


def _without_size(name: str) -> str:
    """``"180 Litre Refuse"`` -> ``"Refuse"``."""
    return re.sub(r"^\d+ Litre ", "", name.strip())


@final
class Source(BaseSource):
    TITLE = "Forest of Dean District Council"
    DESCRIPTION = "Source for Forest of Dean District Council, UK."
    URL = "https://www.fdean.gov.uk/"
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
        "Southfield Road, Coleford": {
            "address": "8 SOUTHFIELD ROAD, COLEFORD, GL16 8BZ"
        },
        "Wynols Close, Broadwell": {
            "address": "36 WYNOLS CLOSE, BROADWELL, COLEFORD, GL16 7RR"
        },
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to the Forest of Dean waste collection enquiry page "
            "(https://community.fdean.gov.uk/s/waste-collection-enquiry) and type "
            "your postcode into the address lookup. Use the full address string "
            "exactly as it is returned by the autocomplete (e.g. "
            "'8 SOUTHFIELD ROAD, COLEFORD, GL16 8BZ')."
        ),
    }

    retrieve = AuraWasteEnquiryRetriever("community.fdean.gov.uk", client_code="FOD")
    parse = AuraWasteTableParser()
    transform = RowTransformer(
        clean=_without_size, type_value_map=_TYPE_MAP, carry_raw_label=True
    )
