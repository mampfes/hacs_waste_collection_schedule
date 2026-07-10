from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.FirmstepSelfService import (
    DerbyshireDalesRowClassifier,
    FirmstepAddressFormRetriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

FORM_URL = (
    "https://selfserve.derbyshiredales.gov.uk/"
    "renderform?k=9644C066D2168A4C21BCDA351DA2642526359DFF&t=103"
)
RENDER_URL = "https://selfserve.derbyshiredales.gov.uk/RenderForm"
ADDRESS_LOOKUP_URL = "https://selfserve.derbyshiredales.gov.uk/core/addresslookup"
ROW_SELECTOR = "div.ss_confPanel div.row[style*='padding-left']"


@final
class Source(BaseSource):
    TITLE = "Derbyshire Dales District Council"
    DESCRIPTION = "Source for derbyshiredales.gov.uk services for Derbyshire Dales, UK."
    URL = "https://www.derbyshiredales.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Matlock": {"address_id": "DE4 3GS"},
        "Bakewell": {"address_id": "U10070089522"},
        "Wirksworth": {"address_id": "U10070097828"},
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
        value_field="FF2924",
        static_fields={
            "FF2924lbltxt": "Collection Address",
            "FF2924-text": "False",
        },
        row_selector=ROW_SELECTOR,
    )
    parse = parsers.HtmlParser(ROW_SELECTOR)
    preprocess = DerbyshireDalesRowClassifier()
    transform = RowTransformer(
        type_value_map={
            "domestic waste": GENERAL_WASTE,
            "recycling waste": RECYCLABLES,
            "food waste": FOOD_WASTE,
            "garden waste": GARDEN_WASTE,
        },
    )

    def __init__(self, address_id: str):
        super().__init__(address_id=address_id)
