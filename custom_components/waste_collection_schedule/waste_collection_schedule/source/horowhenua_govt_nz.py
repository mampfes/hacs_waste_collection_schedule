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
    TITLE = "Horowhenua District Council"
    DESCRIPTION = (
        "Source for Horowhenua District Council Rubbish & Recycling collection."
    )
    URL = "https://www.horowhenua.govt.nz/"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "House-Shannon": {
            "post_code": "4821",
            "town": "Shannon",
            "street_name": "Bryce Street",
            "street_number": "55",
        },
        "House-Levin": {
            "post_code": "5510",
            "town": "Levin",
            "street_name": "McKenzie Street",
            "street_number": "15",
        },
        "Commercial-Foxton": {
            "post_code": "4814",
            "town": "Foxton",
            "street_name": "State Highway 1",
            "street_number": "18",
        },
    }

    PARAMS = (
        address(
            street_field="street_name",
            number="street_number",
            postcode_field="post_code",
            city_field="town",
        ),
    )

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    retrieve = OpenCitiesRetriever(
        domain="https://www.horowhenua.govt.nz",
        address=None,
        address_template="{street_number} {street_name} {town} {post_code}",
        argument="street_name",
        warm_up_url="https://www.horowhenua.govt.nz",
        headers={"user-agent": "Mozilla/5.0"},
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
