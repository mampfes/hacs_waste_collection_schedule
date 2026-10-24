from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.ITouchVision import (
    TYPE_MAP,
    ITouchVisionParser,
    ITouchVisionRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# The published UPRN 10094593823 no longer returns a portal schedule. This
# UPRN is the working Aylesbury Vale case, which the Buckinghamshire form accepts.
_DEPRECATION = "This source is deprecated. Use iapp_iTouchVision instead."


@final
class Source(BaseSource):
    TITLE = "Deprecated: Buckinghamshire"
    DESCRIPTION = "Deprecated: use the iapp_iTouchVision instead."
    URL = "https://chiltern.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_004": {"uprn": 766251559},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Deprecated. Add iTouchVision instead and choose municipality "
            "BUCKINGHAMSHIRE. This entry still accepts a UPRN and reads the "
            "Buckinghamshire bin-day form."
        ),
    }

    retrieve = ITouchVisionRetriever(
        municipality="BUCKINGHAMSHIRE",
        deprecation=_DEPRECATION,
    )
    parse = ITouchVisionParser()
    transform = RowTransformer(type_value_map=TYPE_MAP)
