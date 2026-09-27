import datetime
from typing import ClassVar, final
from urllib.parse import quote
from zoneinfo import ZoneInfo

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import DateFields
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://www.canning.wa.gov.au/api/property-details"
_PERTH = ZoneInfo("Australia/Perth")


def _property_key(response, *, address: str, **_) -> str:
    """The first property the address search returns."""
    properties = response.json()
    if not properties:
        raise SourceArgumentNotFound("address", address)
    return properties[0]["key"]


def _local_date(value: str) -> datetime.date:
    """A UTC timestamp's date in Perth: 16:00 UTC is the next local day."""
    return datetime.datetime.fromisoformat(value).astimezone(_PERTH).date()


@final
class Source(BaseSource):
    TITLE = "City of Canning (WA)"
    DESCRIPTION = "Source for City of Canning, Western Australia"
    URL = "https://www.canning.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"address": "1325 Albany Highway CANNINGTON  6107"},
        "Test_002": {"address": "3 Rossmoyne Drive ROSSMOYNE  6148"},
        "Test_003": {"address": "12 Battersea Road CANNING VALE  6155"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Your address, as it is displayed on the website when showing your collection schedule. Note: There are usually two whitespace characters between the suburb and postal code.",
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda address, **_: f"{_API_URL}/find/{quote(address)}",
                pick=_property_key,
            ),
        ),
        url=lambda property_key, **_: f"{_API_URL}/bins/{property_key}",
        raise_for_status=True,
    )
    parse = parsers.JsonParser()
    preprocess = DateFields(
        fields={
            "rubbishCollectionDate": "Rubbish",
            "recyclingCollectionDate": "Recycling",
            "greenWasteCollectionDates": "Green",
            "junkWasteCollectionDates": "Junk",
        },
        parse_date=lambda value: _local_date(value) if value else None,
    )
    transform = ICSTransformer(
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green": wt.GARDEN_WASTE,
            "Junk": wt.BULKY_WASTE,
        }
    )
