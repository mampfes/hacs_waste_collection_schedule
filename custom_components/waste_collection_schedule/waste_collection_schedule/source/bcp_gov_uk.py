import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

PAGE_URL = "https://bcpportal.bcpcouncil.gov.uk/checkyourbincollection/"

API_URL_REGEX = re.compile(
    r'function fetchBinCollectionData.*?const response = await fetch\("(.*?)"',
    re.MULTILINE | re.DOTALL,
)


def _pick_api_url(response, *_, **__) -> str:
    """The portal page embeds the (signed) Logic App endpoint its script posts to."""
    match = API_URL_REGEX.search(response.text)
    if not match:
        raise ValueError("Could not find API URL in the response.")
    return match.group(1)


@final
class Source(BaseSource):
    TITLE = "BCP Council"
    DESCRIPTION = (
        "Bin collection data for Bournemouth, Christchurch and Poole Council, UK"
    )
    URL = "https://bcpportal.bcpcouncil.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 10013449141},
        "Test_002": {"uprn": "10001085438"},
        "Test_003": {"uprn": "100040567667"},
    }

    PARAMS = (uprn(),)

    retrieve = retrievers.Request(
        lambda api_url, **_: api_url,
        method="POST",
        json=lambda api_url, **params: {"uprn": params["uprn"]},
        before=(retrievers.Lookup(PAGE_URL, pick=_pick_api_url),),
    )

    parse = parsers.JsonParser("data")

    preprocess = ExplodeList("scheduleDateRange", into="date")

    transform = JsonTransformer(
        date_key="date",
        type_key="wasteContainerUsageTypeDescription",
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Food waste": wt.FOOD_WASTE,
        },
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
