from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id, street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Shoalhaven City Council"
    DESCRIPTION = "Source script for shoalhaven.nsw.gov.au"
    URL = "https://www.shoalhaven.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "2 Cherry Plum Way, WORRIGEE": {
            "street_address": "2 Cherry Plum Way, WORRIGEE"
        },
        "10 Station Street, NOWRA": {"street_address": "10 Station Street, NOWRA"},
        "3 The Park Drive, SANCTUARY POINT": {
            "street_address": "3 The Park Drive, SANCTUARY POINT"
        },
        "Elizabeth Dr, VINCENTIA": {
            "geolocation_id": "2ea7b0c7-b627-421d-8436-248b8da384b6"
        },
        "The Park Dr, SANCTUARY POINT": {
            "geolocation_id": "b0b35bab-76c1-4b58-b609-115da3fa3829"
        },
        "Station St, NOWRA": {"geolocation_id": "984061de-cd63-43f4-bbd3-694b4e8af4d5"},
    }

    PARAMS = (
        street_address(field="street_address", optional=True),
        location_id(field="geolocation_id", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address as the council's own address search shows "
        'it, e.g. "2 Cherry Plum Way, WORRIGEE". You can check it on the '
        "<https://www.shoalhaven.nsw.gov.au/My-Area> page. Alternatively give "
        "the Location ID, the council's geolocation ID. It skips the address "
        "lookup and takes precedence when both are given. To find it, open your "
        "browser's developer tools (F12, Network tab), select your address on "
        "the page above and look for the request "
        "`https://www.shoalhaven.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<ID>&ocsvclang=en-AU`. "
        "The value after `geolocationid=` is your Location ID."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    retrieve = OpenCitiesRetriever(
        domain="https://www.shoalhaven.nsw.gov.au",
        address="street_address",
        geolocation_id="geolocation_id",
    )
    parse = OpenCitiesParser(require_date_precise=True)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
