from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = (
    "https://bbaz-as-prod-bartecapi.azurewebsites.net"
    "/api/bincollections/residential/getbyuprn/"
)


@final
class Source(BaseSource):
    TITLE = "Bedford Borough Council"
    DESCRIPTION = "Source for bedford.gov.uk services for Bedford Borough Council, UK."
    URL = "https://bedford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100080009302"},
        "Test_003": {"uprn": "100080018481"},
        "Test_004": {"uprn": "100080023672"},
    }

    PARAMS = (uprn(),)

    # The API wants the UPRN zero-padded to 12 digits, and answers only with
    # the council site as referrer.
    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: f"{_API_URL}{str(uprn).strip().zfill(12)}",
        headers={
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bedford.gov.uk/",
            "Origin": "https://www.bedford.gov.uk",
        },
    )
    # One list of bins per collection day.
    parse = parsers.JsonParser("BinCollections")
    preprocess = preprocessors.FlattenGroups()
    transform = JsonTransformer(
        date_key="JobScheduledStart",
        type_key="BinType",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map={
            "black bin": wt.GENERAL_WASTE,
            "orange bin": wt.RECYCLABLES,
            "green bin": wt.GARDEN_WASTE,
            "caddy bin": wt.FOOD_WASTE,
        },
    )
