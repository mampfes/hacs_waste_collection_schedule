from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    DateFields,
    DefaultPreprocessor,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_parse = date_parsers.for_format("%Y-%m-%d")


@final
class Source(BaseSource):
    TITLE = "City of Ballarat"
    DESCRIPTION = "Source for City of Ballarat rubbish collection."
    URL = "https://www.ballarat.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Clothesline Cafe": {
            "street_address": "202 Humffray Street South BAKERY HILL VIC 3350"
        },
        "Cuthberts Road Milk Bar": {
            "street_address": "27 Cuthberts Road ALFREDTON VIC 3350"
        },
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Check your address on "
            "https://data.ballarat.vic.gov.au/pages/waste-collection-day/ and "
            "enter it as it is listed there."
        ),
    }

    # The city's open-data portal; the best match of the address search
    # carries the next date of each stream in its own field.
    retrieve = HttpGetRetriever(
        url="https://data.ballarat.vic.gov.au/api/records/1.0/search/",
        params=lambda street_address, **_: {
            "dataset": "waste-collection-days",
            "q": street_address,
        },
    )
    parse = parsers.JsonParser("records", 0, "fields")
    preprocess = Compose(
        DefaultPreprocessor(),
        DateFields(
            fields={
                "nextwaste": "waste",
                "nextrecycle": "recycle",
                "nextgreen": "green",
                "next_glass": "glass",
            },
            parse_date=lambda value: _parse(value) if value else None,
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "waste": wt.GENERAL_WASTE,
            "recycle": wt.RECYCLABLES,
            "green": wt.GARDEN_WASTE,
            "glass": wt.GLASS,
        }
    )
