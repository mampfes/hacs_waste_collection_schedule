from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    postcode,
    text_field,
)
from waste_collection_schedule.service.IslFusion import (
    CollectionsParser,
    calendar_retriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Fermanagh and Omagh District Council"
    DESCRIPTION = (
        "Source for the Fermanagh and Omagh District Council, Northern Ireland"
    )
    URL = "https://www.fermanaghomagh.com/"
    COUNTRY = "uk"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "BT78 1RG", "house_number": "1"},
        "Test_002": {"postcode": "BT78 5AA", "house_number": "10"},
        "Test_003": {"property_id": "GMtpf6Tk1glK57Zj"},
    }

    PARAMS = (
        alternatives(
            [text_field("property_id", "Property ID")],
            [postcode(), house_number()],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your postcode and house number (or name), or the property ID "
            "as found in the URL when looking up your bin collection days."
        ),
    }

    retrieve = calendar_retriever("https://fermanaghomagh.isl-fusion.com")
    parse = CollectionsParser()
    transform = RowTransformer(
        type_value_map={
            "Black Landfill": wt.GENERAL_WASTE,
            "Blue Recycling": wt.RECYCLABLES,
            "Brown Composting": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
        }
    )
