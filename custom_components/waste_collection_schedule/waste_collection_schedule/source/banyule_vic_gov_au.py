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
    TITLE = "Banyule City Council"
    DESCRIPTION = "Source for Banyule City Council rubbish collection."
    URL = "https://www.banyule.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Monday A": {"street_address": "6 Mandall Avenue, IVANHOE"},
        "Monday A Geolocation ID": {
            "geolocation_id": "486d9d83-8377-4709-987f-4627beaa0ac8"
        },
        "Monday B": {"street_address": "10 Burke Road North, IVANHOE EAST"},
        "Thursday A": {"street_address": "255 St Helena Road, GREENSBOROUGH"},
        "Thursday B": {"street_address": "35 Para Road, MONTMORENCY"},
    }

    PARAMS = (
        street_address(field="street_address", optional=True),
        location_id(field="geolocation_id", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": "Visit the [Banyule City Council bin collection "
        "services](https://www.banyule.vic.gov.au/Waste-environment/Waste-recycling/Bin-collection-services) "
        "page and search for your address. The street address should exactly "
        "match the address shown in the autocomplete result. For unlisted "
        "addresses use an adjacent listed address. Alternatively give the "
        "Location ID, the council's geolocation ID. It skips the address lookup "
        "and takes precedence when both are given. To find it, open your "
        "browser's developer tools (F12, Network tab), select your address on "
        "the page above and look for the request "
        "`https://www.banyule.vic.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<ID>&ocsvclang=en-AU`. "
        "The value after `geolocationid=` is your Location ID."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.banyule.vic.gov.au",
        address="street_address",
        geolocation_id="geolocation_id",
        warm_up_url="https://www.banyule.vic.gov.au/Waste-environment/Waste-recycling/Bin-collection-services",
        warm_up_before="wasteservices",
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
