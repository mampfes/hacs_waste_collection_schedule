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
    TITLE = "Moorabool Shire Council"
    DESCRIPTION = "Source for Moorabool Shire Council rubbish collection."
    URL = "https://www.moorabool.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Border Inn Hotel": {"address": "139 Main Street Bacchus Marsh 3340"},
        "Bendigo Bank": {"address": "191 Main Street Bacchus Marsh 3340"},
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Go to "
        "<https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day> "
        "and make sure your address matches the auto-complete suggestions."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.moorabool.vic.gov.au",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Accept": "text/plain, */*; q=0.01",
            "Referer": "https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day",
            "X-Requested-With": "XMLHttpRequest",
        },
        strict_address_matching=True,
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            "Garbage collection": wt.GENERAL_WASTE,
            "Recycling collection": wt.RECYCLABLES,
            "Green waste collection": wt.GARDEN_WASTE,
        },
    )
