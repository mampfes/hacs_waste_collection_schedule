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
    TITLE = "Cassowary Coast Regional Council"
    DESCRIPTION = (
        "Source for Cassowary Coast Regional Council, Far North Queensland, Australia."
    )
    URL = "https://www.cassowarycoast.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "10 Bombala Street, Mourilyan": {
            "address": "10 Bombala Street, Mourilyan, 4858"
        }
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter the full service address used by Cassowary Coast Regional "
        "Council, for example '10 Bombala Street, Mourilyan, 4858'."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    retrieve = OpenCitiesRetriever(
        domain="https://www.cassowarycoast.qld.gov.au",
        search_fuzzy=True,
        max_results=1,
        page_link="/Waste-Water-and-Roads/Waste-and-Recycling/Kerbside-Collection",
        headers={
            "accept": "application/json, text/javascript, */*; q=0.01",
            "referer": "https://www.cassowarycoast.qld.gov.au/Waste-Water-and-Roads/Waste-and-Recycling/Kerbside-Collection",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
