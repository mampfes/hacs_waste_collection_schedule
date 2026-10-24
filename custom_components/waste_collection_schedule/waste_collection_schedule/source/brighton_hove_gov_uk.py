from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.BrightonHoveCollections import (
    BrightonHoveParser,
    BrightonHoveRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Brighton & Hove City Council"
    DESCRIPTION = "Source for Brighton & Hove City Council."
    URL = "https://www.brighton-hove.gov.uk/"
    COUNTRY = "uk"
    # A matched property can legitimately have nothing in the council's short
    # window. An unknown postcode or UPRN is raised by the retriever.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "11 West Drive": {"postcode": "BN2 0GD", "uprn": "000022064770"},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your property's UPRN "
            "(https://www.findmyaddress.co.uk/). The council only publishes "
            "the next couple of weeks. Garden waste is listed only when the "
            "property is subscribed."
        ),
    }

    retrieve = BrightonHoveRetriever("https://enviroservices.brighton-hove.gov.uk/")
    parse = BrightonHoveParser()
    transform = ICSTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
