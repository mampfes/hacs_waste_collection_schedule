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
    TITLE = "Logan City Council"
    DESCRIPTION = "Source for Logan City Council rubbish collection."
    URL = "https://www.logan.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Lee Naki's Takeaway": {"property_location": "12 Ashton Street Kingston"},
        "LCC Administration Centre": {
            "property_location": "150 Wembley Road Logan Central"
        },
        "Rochedale South (with green waste)": {
            "property_location": "53 Wendron Street Rochedale South"
        },
    }

    PARAMS = (street_address(field="property_location"),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address as used on the Logan City Council MyLogan "
        "tool (https://www.logan.qld.gov.au/MyLogan), for example '12 Ashton "
        "Street Kingston'."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.logan.qld.gov.au",
        address="property_location",
        max_results=1,
        headers={
            "accept": "application/json, text/javascript, */*; q=0.01",
            "referer": "https://www.logan.qld.gov.au/MyLogan",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser(date_format="%A %d %B %Y")
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
