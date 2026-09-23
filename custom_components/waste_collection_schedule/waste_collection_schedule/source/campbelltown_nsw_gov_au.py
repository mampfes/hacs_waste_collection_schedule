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
    TITLE = "Campbelltown City Council (NSW)"
    DESCRIPTION = "Source for Campbelltown City Council rubbish collection."
    URL = "https://www.campbelltown.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Minto Mall": {
            "post_code": "2566",
            "suburb": "Minto",
            "street_name": "Brookfield Road",
            "street_number": "10",
        },
        "Campbelltown Catholic Club": {
            "post_code": "2560",
            "suburb": "Campbelltown",
            "street_name": "Camden Road",
            "street_number": "20-22",
        },
        "Australia Post Ingleburn": {
            "post_code": "2565",
            "suburb": "INGLEBURN",
            "street_name": "Oxford Road",
            "street_number": "34",
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
        domain="https://www.campbelltown.nsw.gov.au",
        address=None,
        address_template="{street_number} {street_name} {suburb} NSW {post_code}",
        argument="street_name",
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
