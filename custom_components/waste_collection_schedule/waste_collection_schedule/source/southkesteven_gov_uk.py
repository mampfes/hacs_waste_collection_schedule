from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.FirmstepSelfService import (
    FirmstepAddressFormRetriever,
    SouthKestevenRowClassifier,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

FORM_URL = (
    "https://selfservice.southkesteven.gov.uk/"
    "renderform?k=2074C945A63DDC0D18F1EB74DA230AC3122958B1&t=213"
)
RENDER_URL = "https://selfservice.southkesteven.gov.uk/RenderForm"
ADDRESS_LOOKUP_URL = "https://selfservice.southkesteven.gov.uk/core/addresslookup"
ROW_SELECTOR = "table.Alloy-table tr"


@final
class Source(BaseSource):
    TITLE = "South Kesteven District Council"
    DESCRIPTION = "Source for southkesteven.gov.uk services for South Kesteven, UK."
    URL = "https://southkesteven.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Bourne": {"address_id": "PE10 0RX"},
        "Long Bennington": {"address_id": "NG23 5EQ"},
        "Grantham": {"address_id": "NG31 6NP"},
    }

    PARAMS = (text_field("address_id", "UPRN or Postcode"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Your property's UPRN, find it at https://www.findmyaddress.co.uk/. "
            "You can also use a Postcode."
        ),
    }

    retrieve = FirmstepAddressFormRetriever(
        form_url=FORM_URL,
        render_url=RENDER_URL,
        address_lookup_url=ADDRESS_LOOKUP_URL,
        value_field="FF5265",
        static_fields={
            "FF5265lbltxt": "Collection Address",
            "FF5265searchnlpg": "False",
            "FF5265manualaddressentry": "False",
            "FF5265classification": "",
        },
        row_selector="table.Alloy-table tr td.Alloy-table-col",
    )
    parse = parsers.HtmlParser(ROW_SELECTOR)
    preprocess = SouthKestevenRowClassifier()
    transform = RowTransformer(
        type_value_map={
            "black": GENERAL_WASTE,
            "gray": RECYCLABLES,
            "green": ORGANIC,
            "purple": PAPER,
        },
    )

    def __init__(self, address_id: str):
        super().__init__(address_id=address_id)
