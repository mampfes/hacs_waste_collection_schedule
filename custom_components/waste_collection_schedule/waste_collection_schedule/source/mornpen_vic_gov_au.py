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
    TITLE = "Mornington Peninsula Shire Council"
    DESCRIPTION = "Source for Mornington Peninsula Shire Council rubbish collection."
    URL = "https://www.mornpen.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Main Ridge Pony Club": {
            "street_address": "305 Baldrys Rd Main Ridge VIC 3928"
        },
        "Laneway Espresso Dromana": {
            "street_address": "167 Point Nepean Rd Dromana VIC 3936"
        },
        "Pt. Leo Estate Merricks": {
            "street_address": "3649 Frankston-Flinders Rd Merricks VIC 3916"
        },
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.mornpen.vic.gov.au",
        address="street_address",
        warm_up_url="https://www.mornpen.vic.gov.au/Your-Property/Rubbish-Recycling/Bins/Find-your-bin-day",
        # The plain search needs every token to match, and the council spells
        # the state "VICTORIA": "... Main Ridge VIC 3928" finds nothing there.
        search_fuzzy=True,
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            "Household rubbish bin": wt.GENERAL_WASTE,
            "Recycling bin": wt.RECYCLABLES,
            "Green waste bin": wt.GARDEN_WASTE,
            "Burning off": None,
        },
    )
