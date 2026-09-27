from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import coords
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Mitchell Shire Council"
    DESCRIPTION = "Source for Mitchell Shire Council, Victoria, Australia."
    URL = "https://www.mitchellshire.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Wallan": {"lat": -37.4195459, "lon": 144.9592853},
        "Beveridge": {"lat": -37.48012709087705, "lon": 144.94518706976186},
        "McDonalds Wallan": {"lat": -37.41290975665613, "lon": 144.97998167557827},
    }

    PARAMS = (coords(),)

    retrieve = HttpGetRetriever(
        url="https://www.mitchellshire.vic.gov.au/simple-gov-app/api/resources/bin-collections/search",
        params=lambda lat, lon, **_: {"lat": lat, "lng": lon},
    )
    parse = parsers.JsonParser("data", expected_values=None)
    # Each bin lists its collection dates.
    preprocess = ExplodeList("collectionDates", into="collection")
    transform = JsonTransformer(
        date_key=lambda record: record["collection"]["date"],
        type_key="title",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "General Rubbish": wt.GENERAL_WASTE,
            "Mixed Recycling": wt.RECYCLABLES,
            "Food and Garden Organics": wt.ORGANIC,
            "Glass Recycling": wt.GLASS,
        },
    )
