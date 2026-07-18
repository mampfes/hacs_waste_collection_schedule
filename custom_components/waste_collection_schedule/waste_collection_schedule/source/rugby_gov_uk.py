from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.uk_cloud9_apps import (
    Cloud9Parser,
    Cloud9Retriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)


@final
class Source(BaseSource):
    TITLE = "Rugby Borough Council"
    DESCRIPTION = "Source for Rugby Borough Council, UK."
    URL = "https://www.rugby.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 100070200377},
        "Test_002": {"uprn": "100070200372"},
        "Test_003": {"uprn": "010010521297"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by entering "
            "your address details."
        ),
    }

    retrieve = Cloud9Retriever("rugby", uprn_field="uprn")
    parse = Cloud9Parser()
    transform = RowTransformer(
        type_value_map={
            "Black refuse bin": GENERAL_WASTE,
            "Blue-lid recycling bin": RECYCLABLES,
            "Food caddy": FOOD_WASTE,
            "Green garden waste bin": GARDEN_WASTE,
        },
    )

    def __init__(self, uprn):
        super().__init__(uprn=uprn)
