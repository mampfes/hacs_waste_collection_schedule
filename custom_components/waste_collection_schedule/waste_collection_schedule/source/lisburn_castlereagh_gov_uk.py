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
    TITLE = "Lisburn and Castlereagh City Council"
    DESCRIPTION = "Source for the Lisburn and Castlereagh City Council"
    URL = "https://lisburncastlereagh.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    # The recycling bin and the wheelie box can fall on one day; the original
    # label stays in the description and the duplicates collapse by default.
    IGNORE_DUPLICATES_DEFAULT = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "BT28 1AG", "house_number": "19A"},
        "Test_002": {"postcode": "BT26 6AB", "house_number": "31"},
        "Test_003": {"postcode": "BT26 6AB", "house_number": 15},
        "Test_004": {"property_id": "RTTKBJY77wmTr5wP"},
        "Test_005": {"property_id": "6opWbT5hi9odCQ2u"},
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

    retrieve = calendar_retriever("https://lisburn.isl-fusion.com")
    parse = CollectionsParser()
    transform = RowTransformer(
        type_value_map={
            "ResidualBin": wt.GENERAL_WASTE,
            "RecycleBin": wt.RECYCLABLES,
            "WheelieBox": wt.RECYCLABLES,
            "BrownBin": wt.GARDEN_WASTE,
            "FoodWaste": wt.FOOD_WASTE,
        },
        carry_raw_label=True,
    )
