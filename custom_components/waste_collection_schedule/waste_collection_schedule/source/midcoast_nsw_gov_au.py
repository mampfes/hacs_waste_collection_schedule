from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "MidCoast Council"
    DESCRIPTION = "Source for MidCoast Council (NSW) rubbish collection."
    URL = "https://www.midcoast.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Randomly Selected Address": {"street_address": "101 Goldens Road, FORSTER"}
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.midcoast.nsw.gov.au",
        address="street_address",
        warm_up_url="https://www.midcoast.nsw.gov.au/",
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
