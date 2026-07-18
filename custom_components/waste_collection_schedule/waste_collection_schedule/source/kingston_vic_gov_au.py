from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import address
from waste_collection_schedule.service.WhatBinDay import (
    TYPE_VALUE_MAP,
    WhatBinDayParser,
    WhatBinDayRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

TITLE = "City of Kingston"
DESCRIPTION = "Source for City of Kingston (VIC) waste collection."
URL = "https://www.kingston.vic.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "randomHouse": {
        "street_number": "30C",
        "street_name": "Oakes Avenue",
        "suburb": "CLAYTON SOUTH",
        "post_code": "3169",
    },
    "randomAppartment": {
        "street_number": "1/51",
        "street_name": "Whatley Street",
        "suburb": "CARRUM",
        "post_code": "3197",
    },
    "randomMultiunit": {
        "street_number": "1/1-5",
        "street_name": "Station Street",
        "suburb": "MOORABBIN",
        "post_code": "3189",
    },
}


def _location_key(parts: dict) -> str:
    return (
        f"{parts['street_number']}_{parts['street_name']}_"
        f"{parts['suburb']}_{parts['post_code']}"
    )


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY

    TEST_CASES = TEST_CASES

    # An address-lookup source: an empty result means the address didn't
    # resolve, so surface a clear error rather than a silently-empty calendar.
    RAISE_ON_EMPTY = True

    PARAMS = (
        address(
            street_field="street_name",
            number="street_number",
            postcode_field="post_code",
            city_field="suburb",
        ),
    )

    # Kingston's fortnightly recycling / food-and-garden-waste roster (and even
    # the weekday of collection) differs from street to street, so a single
    # fixed coordinate cannot be used for every address: the upstream API
    # resolves the applicable roster from the submitted coordinates, not from
    # the address text fields. Hence geocode=True.
    # See https://github.com/mampfes/hacs_waste_collection_schedule/issues/6772
    retrieve = WhatBinDayRetriever(
        location_key=_location_key,
        state="VIC",
        geocode=True,
    )
    parse = WhatBinDayParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)
