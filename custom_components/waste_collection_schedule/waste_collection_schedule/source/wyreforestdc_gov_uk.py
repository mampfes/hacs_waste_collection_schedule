from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, customer_number, street
from waste_collection_schedule.service.WyreForest import (
    WyreForestParser,
    WyreForestRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "rubbish": wt.GENERAL_WASTE,
    "recycling": wt.RECYCLABLES,
    "garden waste": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Wyre Forest District Council"
    DESCRIPTION = "Source for wyreforestdc.gov.uk, Wyre Forest District Council, UK"
    URL = "https://www.wyreforestdc.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "2 Kinver Avenue, Kidderminster": {
            "street": "hilltop avenue",
            "town": "BEWDLEY",
            "garden_cutomer": "308072",
        },
        "Worcester Street, Stourport (no garden waste)": {
            "street": "WORCESTER STREET",
            "town": "STOURPORT ON SEVERN",
        },
    }

    PARAMS = (
        street(field="street"),
        city(field="town"),
        customer_number(field="garden_cutomer", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Street and town must match the URL parameters you get when clicking an "
            "address at https://forms.wyreforestdc.gov.uk/querybin.asp. The garden "
            "waste customer number (garden_cutomer) is only needed for garden waste "
            "collections: go to https://forms.wyreforestdc.gov.uk/gardenwastechecker, "
            "enter your postcode and, before pressing Select on your address, open "
            "your browser's developer tools (F12) and its network tab. Pressing "
            "Select sends a POST request to "
            "https://forms.wyreforestdc.gov.uk/GardenWasteChecker/Home/Details; the "
            "customer number is the CUST_No value in its payload."
        ),
    }

    retrieve = WyreForestRetriever()
    parse = WyreForestParser()
    transform = RowTransformer(type_value_map=_TYPE_MAP)
