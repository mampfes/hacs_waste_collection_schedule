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
    TITLE = "Town of Cambridge (WA)"
    DESCRIPTION = "Source for Town of Cambridge (Western Australia) rubbish collection."
    URL = "https://www.cambridge.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Geolocation ID": {"geolocation_id": "c70848c4-fe33-431d-85aa-987ff8b155cb"},
        "Cambridge Library": {"street_address": "99 The Boulevard, FLOREAT 6014"},
    }

    PARAMS = (
        street_address(field="street_address", optional=True),
        location_id(field="geolocation_id", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": "Visit the [Town of Cambridge Find My Bin "
        "Day](https://www.cambridge.wa.gov.au/Residents/Waste-Recycling/Find-My-Bin-Day) "
        "page and search for your address. The street address should exactly "
        "match the address shown in the autocomplete result. For unlisted "
        "addresses use an adjacent listed address. Alternatively give the "
        "Location ID, the council's geolocation ID. It skips the address lookup "
        "and takes precedence when both are given. To find it, open your "
        "browser's developer tools (F12, Network tab), select your address on "
        "the page above and look for the request "
        "`https://www.cambridge.wa.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<ID>&ocsvclang=en-AU`. "
        "The value after `geolocationid=` is your Location ID."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.cambridge.wa.gov.au",
        address="street_address",
        geolocation_id="geolocation_id",
        warm_up_url="https://www.cambridge.wa.gov.au/Residents/Waste-Recycling/Find-My-Bin-Day",
        warm_up_before="wasteservices",
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
