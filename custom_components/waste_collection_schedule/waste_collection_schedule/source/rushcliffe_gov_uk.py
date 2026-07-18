from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.service.FirmstepSelfService import (
    RushcliffeAddressRetriever,
    RushcliffePanelParser,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    PAPER,
)

FORM_URL = "https://selfservice.rushcliffe.gov.uk/renderform.aspx?t=1242&k=86BDCD8DE8D868B9E23D10842A7A4FE0F1023CCA"
ADDRESS_LOOKUP_URL = "https://selfservice.rushcliffe.gov.uk/core/addresslookup"
FORM_POST_URL = "https://selfservice.rushcliffe.gov.uk/renderform/Form"

STATIC_FIELDS = {
    "FormGuid": "aaa360e6-240e-46e9-b651-bd7fb8091354",
    "ObjectTemplateID": "1242",
    "Trigger": "submit",
    "CurrentSectionID": 1397,
    "TriggerCtl": "",
}


@final
class Source(BaseSource):
    TITLE = "Rushcliffe Brough Council"
    DESCRIPTION = "Source for Rushcliffe Brough Council."
    URL = "https://www.rushcliffe.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "NG12 5FE 2 Church Drive, Keyworth, NOTTINGHAM, NG12 5FE": {
            "postcode": "NG12 5FE",
            "address": "2 Church Drive, Keyworth, NOTTINGHAM, NG12 5FE",
        }
    }

    PARAMS = (postcode(), text_field("address", "Address"))

    retrieve = RushcliffeAddressRetriever(
        form_url=FORM_URL,
        address_lookup_url=ADDRESS_LOOKUP_URL,
        form_post_url=FORM_POST_URL,
        static_fields=STATIC_FIELDS,
        uprn_field="FF3518",
    )
    parse = RushcliffePanelParser()
    transform = RowTransformer(
        type_value_map={
            "grey": GENERAL_WASTE,
            "garden waste": GARDEN_WASTE,
            "blue": PAPER,
            "glass": GLASS,
        },
    )

    def __init__(self, postcode: str, address: str):
        super().__init__(postcode=postcode, address=address)
