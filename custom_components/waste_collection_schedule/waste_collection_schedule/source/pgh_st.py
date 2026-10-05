from typing import ClassVar, final
from urllib.parse import quote

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.preprocessors import (
    Compose,
    DateFields,
    DefaultPreprocessor,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_parse = date_parsers.for_format("%m-%d-%Y")


def _url(house_number, street_name, zipcode, **_) -> str:
    street_name = quote(str(street_name).replace(".", "").strip())
    return f"https://pgh.st/locate/{house_number}/{street_name}/{zipcode}"


@final
class Source(BaseSource):
    TITLE = "City of Pittsburgh"
    DESCRIPTION = "Source for PGH.ST services for the city of Pittsburgh, PA, USA."
    URL = "https://www.pgh.st"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Pittsburgh, Negley": {
            "house_number": 800,
            "street_name": "Negley",
            "zipcode": 15232,
        },
    }

    PARAMS = (house_number(), street("street_name"), text_field("zipcode", "ZIP code"))

    retrieve = HttpGetRetriever(url=_url)
    # The first match carries the next date of each stream in its own field.
    parse = parsers.JsonParser(0)
    preprocess = Compose(
        DefaultPreprocessor(),
        DateFields(
            fields={
                "next_pickup_date": "Trash",
                "next_recycling_date": "Recycling",
                "next_yard_date": "Yard Waste",
            },
            parse_date=lambda value: _parse(value) if value else None,
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Trash": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Yard Waste": wt.GARDEN_WASTE,
        }
    )
