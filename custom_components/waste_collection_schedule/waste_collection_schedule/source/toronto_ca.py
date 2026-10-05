from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.TorontoSwms import (
    TorontoSwmsParser,
    TorontoSwmsRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Toronto (ON)"
    DESCRIPTION = "Source for Toronto waste collection"
    URL = "https://www.toronto.ca"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "224 Wallace Ave": {"street_address": "224 Wallace Ave"},
        "324 Weston Rd": {"street_address": "324 Weston Rd"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as the City of Toronto writes it, for "
            "example '224 Wallace Ave'. The first match of the city's address "
            "search is used."
        ),
    }

    retrieve = TorontoSwmsRetriever(address="street_address")
    parse = TorontoSwmsParser()
    transform = ICSTransformer(
        type_value_map={
            "GreenBin": wt.ORGANIC,
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "YardWaste": wt.GARDEN_WASTE,
            "ChristmasTree": wt.OTHER,
        },
        carry_raw_label=True,
    )
