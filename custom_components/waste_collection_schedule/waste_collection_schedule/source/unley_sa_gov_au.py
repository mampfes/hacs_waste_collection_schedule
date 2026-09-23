from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Unley City Council (SA)"
    DESCRIPTION = "Source for Unley City Council rubbish collection."
    URL = "https://www.unley.sa.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test1": {
            "post_code": "5061",
            "suburb": "Malvern",
            "street_name": "Wattle Street",
            "street_number": "188",
        },
        "Test2": {
            "post_code": 5061,
            "suburb": "Unley",
            "street_name": "Unley Road",
            "street_number": "192",
        },
        "Test3": {
            "post_code": "5063",
            "suburb": "Parkside",
            "street_name": "Castle Street",
            "street_number": 63,
        },
    }

    PARAMS = (
        address(
            street_field="street_name",
            number="street_number",
            postcode_field="post_code",
            city_field="suburb",
        ),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.OTHER,
    ]

    retrieve = OpenCitiesRetriever(
        domain="https://www.unley.sa.gov.au",
        address=None,
        address_template="{street_number} {street_name} {suburb} SA {post_code}",
        argument="street_name",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) "
            "Gecko/20100101 Firefox/133.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            "General Waste (Blue Bin)": wt.GENERAL_WASTE,
            "General Waste FOGO (Blue Bin)": wt.GENERAL_WASTE,
            "Organic Waste (Green or Grey Bin)": wt.ORGANIC,
            "Organic Waste FOGO (Green or Grey Bin)": wt.ORGANIC,
            "Recycling (Yellow Lid Bin)": wt.RECYCLABLES,
            "Residential Street Cleaning": wt.OTHER,
        },
    )
