from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import address
from waste_collection_schedule.service.OpenCities import (
    TYPE_VALUE_MAP,
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "City of Ryde (NSW)"
    DESCRIPTION = "Source for City of Ryde rubbish collection."
    URL = "https://www.ryde.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Ryde Aquatic Centre": {
            "post_code": "2112",
            "suburb": "Ryde",
            "street_name": "Victoria Road",
            "street_number": "504",
        },
        "Harris Farm Markets Boronia Park": {
            "post_code": "2111",
            "suburb": "Gladesville",
            "street_name": "Pittwater Road",
            "street_number": "128",
        },
        "Eastwood Shopping Centre": {
            "post_code": "2122",
            "suburb": "Eastwood",
            "street_name": "Rowe Street",
            "street_number": "152",
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

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.ryde.nsw.gov.au",
        address=None,
        address_template="{street_number} {street_name} {suburb} {post_code}",
        argument="street_name",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Accept": "text/plain, */*; q=0.01",
            "Referer": "https://www.ryde.nsw.gov.au/Environment-and-Waste/Waste-and-Recycling",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            **TYPE_VALUE_MAP,
        },
    )
