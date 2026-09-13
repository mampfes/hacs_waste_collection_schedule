from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.FirmstepSelfService import (
    BartecTableParser,
    RushcliffeAddressRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

FORM_URL = "https://selfservice.broxtowe.gov.uk/renderform?t=217&k=9D2EF214E144EE796430597FB475C3892C43C528"
ADDRESS_LOOKUP_URL = "https://selfservice.broxtowe.gov.uk/core/addresslookup"
FORM_POST_URL = "https://selfservice.broxtowe.gov.uk/RenderForm"

# Unlike rushcliffe_gov_uk, this council's FormGuid (and every other hidden
# field) is regenerated per session rather than staying constant, so every
# field is re-scraped fresh on each request; only Trigger/TriggerCtl are
# overridden on top (the scraped page's own values are empty).
STATIC_FIELDS = {
    "Trigger": "submit",
    "TriggerCtl": "",
}


@final
class Source(BaseSource):
    TITLE = "Broxtowe Borough Council"
    DESCRIPTION = "Source for Broxtowe Borough Council."
    URL = "https://www.broxtowe.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "100031343805 NG9 2NL": {"uprn": 100031343805, "postcode": "NG9 2NL"},
        "100031514955 NG9 4DU": {"uprn": " 100031308988", "postcode": "NG9 4DU"},
        "U100031514955 NG9 4DU": {"uprn": "U100031308988 ", "postcode": "NG9 4DU"},
    }

    PARAMS = (uprn(), postcode())

    # Resolve postcode+UPRN to a Firmstep address record via the shared
    # addresslookup retriever (broxtowe supplies a UPRN directly rather than
    # free-text address, so `uprn_param` selects that matching mode over the
    # default fuzzy-address one), then decode the Bartec results table.
    retrieve = RushcliffeAddressRetriever(
        form_url=FORM_URL,
        address_lookup_url=ADDRESS_LOOKUP_URL,
        form_post_url=FORM_POST_URL,
        static_fields=STATIC_FIELDS,
        refetch_all_fields=True,
        uprn_field="FF5683",
        uprn_param="uprn",
    )
    parse = BartecTableParser()
    # Bartec's own row labels carry a size/container suffix (e.g. "GREEN
    # 240L", "GLASS BAG"); only the leading colour/material word identifies
    # the bin.
    transform = RowTransformer(
        clean=lambda label: label.split(" ")[0],
        type_value_map={
            "black": wt.GENERAL_WASTE,
            "glass": wt.GLASS,
            "green": wt.ORGANIC,
            "brown": wt.GARDEN_WASTE,
        },
    )
