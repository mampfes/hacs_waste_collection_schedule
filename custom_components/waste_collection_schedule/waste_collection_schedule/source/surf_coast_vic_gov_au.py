from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import address
from waste_collection_schedule.service.WhatBinDay import (
    TYPE_VALUE_MAP,
    WhatBinDayParser,
    WhatBinDayRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

TITLE = "Surf Coast Shire"
DESCRIPTION = "Source for Surf Coast Shire (VIC) waste collection."
URL = "https://www.surfcoast.vic.gov.au"
COUNTRY = "au"

HOWTO = {
    "en": (
        "Visit the Surf Coast Shire 'Bin collection calendars' page "
        "(https://www.surfcoast.vic.gov.au/Property/Waste-and-recycling/"
        "Kerbside-bins/Bin-collection-calendars), search for your address, "
        "then enter the street number, street name, suburb and postcode as "
        "they appear there."
    )
}

TEST_CASES = {
    "Bell Street Torquay": {
        "street_number": "20",
        "street_name": "Bell Street",
        "suburb": "Torquay",
        "post_code": "3228",
    },
    "Mountjoy Parade Lorne": {
        "street_number": "1",
        "street_name": "Mountjoy Parade",
        "suburb": "Lorne",
        "post_code": "3232",
    },
    "Noble Street Anglesea": {
        "street_number": "1",
        "street_name": "Noble Street",
        "suburb": "Anglesea",
        "post_code": "3230",
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
    HOWTO = HOWTO

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

    # Three provider quirks, each a declared option on the shared component:
    # * geocode=True: a generic Victorian coordinate resolves to no bin service
    #   here, so the roster lookup needs coordinates near the property itself.
    # * suburb_case="title": the backend matches the suburb case-sensitively
    #   against a dataset holding "Torquay", not "TORQUAY".
    # * state_long_name="Victoria": this backend wants the full state name as
    #   the administrative_area_level_1 long name, with "VIC" as the short one.
    retrieve = WhatBinDayRetriever(
        location_key=_location_key,
        state="VIC",
        state_long_name="Victoria",
        suburb_case="title",
        geocode=True,
        app_package="com.socketsoftware.whatbinday.surfcoast",
    )
    parse = WhatBinDayParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)
