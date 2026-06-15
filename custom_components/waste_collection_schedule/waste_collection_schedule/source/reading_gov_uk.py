from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Demonstrates: JsonTransformer + a configured HttpGetRetriever
# Notable: API embeds the UPRN in the URL path, so the retriever's URL is a
# callable resolved against source.params. parsers.JsonParser("collections")
# drills into the nested array.


class Source(BaseSource):
    TITLE = "Reading Council"
    DESCRIPTION = "Source for reading.gov.uk services for Reading Council."
    URL = "https://reading.gov.uk"
    COUNTRY = "uk"

    TEST_CASES = {
        "known_uprn": {"uprn": "310027679"},
        "known_uprn as number": {"uprn": 310027679},
    }

    PARAMS = [uprn()]

    retrieve = retrievers.HttpGetRetriever(
        url=lambda uprn: f"https://api.reading.gov.uk/api/collections/{uprn}"
    )
    parse = parsers.JsonParser("collections")

    transformer = JsonTransformer(
        date_key="date",
        type_key="service",
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
        type_value_map={
            "Domestic Waste Collection Service": GENERAL_WASTE,
            "Recycling Collection Service": RECYCLABLES,
            "Food Waste Collection Service": FOOD_WASTE,
            "Garden Waste Collection Service": GARDEN_WASTE,
        },
    )
