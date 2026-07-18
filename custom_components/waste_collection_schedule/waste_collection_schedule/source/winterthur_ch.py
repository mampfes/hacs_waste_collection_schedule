from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.service.A_region_ch import (
    TYPE_VALUE_MAP,
    ARegionIcsParser,
    ARegionRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

TITLE = "Winterthur"
DESCRIPTION = "Source for Winterthur."
URL = "https://winterthur.ch/"
COUNTRY = "ch"

TEST_CASES = {"Am Iberghang": {"street": "Am Iberghang"}}

SEARCH_URL = "https://m.winterthur.ch/api/v1/callmethod/trash/asyncLookupStreet?usid=9749&container=1066394&uri=/index.php?apid=737670"

# Winterthur's ICS summaries carry a "Tour N " prefix and a "ganze Stadt"
# suffix that no other A-Region/CityMobile provider has; trim them so the
# label passed to the transformer is the bare waste-type name.
TITLE_REGEX = r"(?:Tour \d{1,2} )?(.*?)(?=\s*ganze Stadt|$)"


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY

    TEST_CASES = TEST_CASES

    PARAMS = (street(field="street"),)

    retrieve = ARegionRetriever(service="winterthur", search_url=SEARCH_URL)
    parse = ARegionIcsParser(regex=TITLE_REGEX)
    transform = ICSTransformer(type_value_map=TYPE_VALUE_MAP)
