from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    street,
    text_field,
)
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.service.WhitespaceWRP import (
    WhitespaceParser,
    WhitespaceRetriever,
)
from waste_collection_schedule.transformers import RowTransformer, label_cleaner

# Declarative source on the shared Whitespace WRP components (WhitespaceRetriever
# + WhitespaceParser). A RowTransformer maps the council's open-ended type labels
# onto canonical WasteTypes; the legacy ``address_name_numer`` spelling is kept so
# existing configurations continue to work.

_TYPE_MAP = {
    "Domestic Waste": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden Waste": wt.GARDEN_WASTE,
    "Food Waste": wt.FOOD_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Waverley Borough Council"
    DESCRIPTION = (
        "Source for www.waverley.gov.uk services for Waverley Borough Council."
    )
    URL = "https://waverley.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]
    API_URL = "https://wav-wrp.whitespacews.com/"

    TEST_CASES: ClassVar[dict] = {
        "Example": {
            "address_postcode": "GU8 5QQ",
            "address_name_numer": "1",
            "address_street": "Gasden Drive",
        },
        "Example No Postcode Space": {
            "address_postcode": "GU85QQ",
            "address_name_numer": "1",
            "address_street": "Gasden Drive",
        },
    }

    PARAMS = (
        text_field("address_postcode", term=POSTCODE),
        text_field("address_name_numer", "House name/number", optional=True),
        street(field="address_street", optional=True),
        text_field("street_town", "Town", optional=True),
    )

    retrieve = WhitespaceRetriever(
        name_number="address_name_numer",
        postcode="address_postcode",
        street="address_street",
        town="street_town",
    )
    parse = WhitespaceParser()
    transform = RowTransformer(
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=label_cleaner(strip_suffixes=[" Collection Service"]),
        skip_unparseable_dates=True,
    )

    def __init__(
        self,
        address_name_numer=None,
        address_street=None,
        street_town=None,
        address_postcode=None,
    ):
        super().__init__(
            address_postcode=address_postcode,
            address_name_numer=address_name_numer,
            address_street=address_street,
            street_town=street_town,
        )
