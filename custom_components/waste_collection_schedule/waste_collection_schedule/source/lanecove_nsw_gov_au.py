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
    TITLE = "Lane Cove Council"
    DESCRIPTION = "Source for Lane Cove Council rubbish collection."
    URL = "https://www.lanecove.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "17 Moore ST": {"address": "17 Moore ST LANE COVE WEST, 2066"},
        "1 Austin St": {"address": "1 Austin ST LANE COVE, 2066"},
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Visit the Lane Cove Council website and search for your address. Use "
        "the exact address shown in the autocomplete result."
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    retrieve = OpenCitiesRetriever(
        domain="https://www.lanecove.nsw.gov.au",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Accept": "text/plain, */*; q=0.01",
            "Referer": "https://www.lanecove.nsw.gov.au/Services/Waste-and-Recycling/Waste-Collection-Calendar",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            "Container Recycling": wt.RECYCLABLES,
            "General Waste & Food Waste": wt.GENERAL_WASTE,
            "Paper and Cardboard Recycling": wt.PAPER,
        },
    )
