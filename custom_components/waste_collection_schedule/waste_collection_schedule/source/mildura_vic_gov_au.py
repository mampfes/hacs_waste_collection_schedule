from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    TYPE_VALUE_MAP,
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Mildura Rural City Council"
    DESCRIPTION = "Source for Mildura Rural City Council waste collection."
    URL = "https://www.mildura.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Stockmans Drive": {"street_address": "1 Stockmans Drive, Irymple VIC 3498"},
        "Deakin Avenue": {"street_address": "76 Deakin Avenue, Mildura VIC 3500"},
    }

    PARAMS = (street_address(field="street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Go to <https://www.mildura.vic.gov.au/Explore/My-Neighbourhood> and "
        "make sure your address matches the auto-complete suggestions."
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GLASS,
    ]

    retrieve = OpenCitiesRetriever(
        domain="https://www.mildura.vic.gov.au",
        address="street_address",
        headers={
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "accept": "text/plain, */*; q=0.01",
            "Referer": "https://www.mildura.vic.gov.au/Services/Waste-and-Recycling/My-bins/Find-your-bin-day",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            **TYPE_VALUE_MAP,
        },
    )
