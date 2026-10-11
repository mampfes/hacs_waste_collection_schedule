from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, street, text_field
from waste_collection_schedule.service.WhitespaceWRP import (
    WhitespaceParser,
    WhitespaceRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Domestic Waste": wt.GENERAL_WASTE,
    "Food Waste": wt.FOOD_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden Waste": wt.GARDEN_WASTE,
}


def _clean_collection_type(type_text: str) -> str:
    return type_text.removesuffix(" Collection Service").strip()


@final
class Source(BaseSource):
    TITLE = "Norwich City Council"
    DESCRIPTION = (
        "Source for Norwich City Council bin collection via Whitespace BNR platform"
    )
    URL = "https://www.norwich.gov.uk/bins-and-recycling"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
    ]
    API_URL = "https://bnr-wrp.whitespacews.com"

    TEST_CASES: ClassVar[dict] = {
        "GoodExample": {
            "property_name_or_number": "33",
            "street_name": "Carrow Road",
            "postcode": "NR1 1HS",
        },
        "FlatAddress": {
            "property_name_or_number": "Flat 1",
            "street_name": "Unthank Road",
            "postcode": "NR2 2RN",
        },
        "UncompletedRoadName": {
            "property_name_or_number": "18",
            "street_name": "Aylsham",
            "postcode": "NR3 3HG",
        },
        "PostcodeMissingSpace": {
            "property_name_or_number": "258",
            "street_name": "North Park Avenue",
            "postcode": "NR47ED",
        },
    }

    PARAMS = (
        text_field("property_name_or_number", "Property name or number"),
        street("street_name"),
        postcode(),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide the house name or number, the street and the postcode as "
            "shown on the council's bin-day lookup."
        ),
    }

    retrieve = WhitespaceRetriever(
        name_number="property_name_or_number",
        postcode="postcode",
        street="street_name",
    )
    parse = WhitespaceParser()
    transform = RowTransformer(
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=_clean_collection_type,
        skip_unparseable_dates=True,
    )
