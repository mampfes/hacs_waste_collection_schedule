from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Blacktown City Council (NSW)"
    DESCRIPTION = "Source for Blacktown City Council rubbish collection."
    URL = "https://www.blacktown.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Rooty Hill Tennis & Squash Centre": {
            "post_code": "2766",
            "suburb": "Rooty Hill",
            "street_name": "Learmonth St",
            "street_number": "13-15",
        },
        "Workers Blacktown": {
            "post_code": "2148",
            "suburb": "Blacktown",
            "street_name": "Campbell Street",
            "street_number": "18",
        },
        "Hythe St": {
            "post_code": "2770",
            "suburb": "Mount Druitt",
            "street_name": "Hythe St",
            "street_number": "9-11",
        },
        "Issue#4434": {
            "post_code": "2762",
            "suburb": "Tallawong",
            "street_name": "Coffey St",
            "street_number": "13",
        },
    }

    PARAMS = (
        address(
            street_field="street_name",
            number="street_number",
            postcode_field="post_code",
            city_field="suburb",
        ),
    )

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    retrieve = OpenCitiesRetriever(
        domain="https://www.blacktown.nsw.gov.au",
        address=None,
        address_template="{street_number} {street_name}, {suburb} NSW {post_code}",
        argument="street_name",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Accept": "text/plain, */*; q=0.01",
            "Referer": "https://www.blacktown.nsw.gov.au/Services/Waste-services-and-collection/Bin-collection-and-new-service-delivery-days",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
