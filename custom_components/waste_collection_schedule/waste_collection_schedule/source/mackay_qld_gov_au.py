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
    TITLE = "Mackay Regional Council"
    DESCRIPTION = "Source for Mackay Regional Council rubbish collection."
    URL = "https://www.mackay.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Mackay (Monday)": {"address": "77 Wood Street Mackay"},
        "West Mackay (Thursday)": {"address": "115 Nebo Road West Mackay"},
        "Sarina Beach (Wednesday)": {"address": "891 Sarina Beach Road Sarina Beach"},
        "Alligator Creek (Tuesday)": {"address": "184 Hay Point Road Alligator Creek"},
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address as used on the council's rubbish and bins "
        "page (https://www.mackay.qld.gov.au/residents/services/waste), for "
        "example '77 Wood Street Mackay'."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    retrieve = OpenCitiesRetriever(
        domain="https://www.mackay.qld.gov.au",
        max_results=1,
        headers={
            "accept": "application/json, text/javascript, */*; q=0.01",
            "referer": "https://www.mackay.qld.gov.au/residents/services/waste",
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
