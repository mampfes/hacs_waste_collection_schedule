import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import JsonTransformer

# The council's API answers one calendar month per request, as a list of weekday
# slots (most of them null) each holding the bins collected that day. A year of
# schedule is therefore twelve requests, one response each, flattened into the
# ordinary record stream.

_API_URL = "https://mybins.blackburn.gov.uk/api/mybins/getbincollectiondays"
_MONTHS = 12


def _month_urls(source, _context) -> list[str]:
    """One request URL per month, from the current month on."""
    today = datetime.date.today()
    uprn_value = source.params["uprn"]
    urls = []
    for offset in range(_MONTHS):
        index = today.month - 1 + offset
        year, month = today.year + index // 12, index % 12 + 1
        urls.append(f"{_API_URL}?month={month}&year={year}&uprn={uprn_value}")
    return urls


@final
class Source(BaseSource):
    TITLE = "Blackburn with Darwen Borough Council"
    DESCRIPTION = "Source for mybins.blackburn.gov.uk services for Blackburn with Darwen Borough Council, UK."
    URL = "https://blackburn.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    # The internal and external food caddies are both collected with the food
    # waste, so they can share a day.
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "10091617919"},
        "Test_002": {"uprn": "100010732130"},
        "Test_003": {"uprn": 100010729702},
        "Test_004": {"uprn": 100010751876},
    }

    PARAMS = (uprn(),)

    retrieve = retrievers.FanOutRetriever(targets=_month_urls)
    parse = parsers.EachResponse(parsers.JsonParser("BinCollectionDays"))
    preprocess = preprocessors.FlattenGroups()
    transform = JsonTransformer(
        date_key="CollectionDate",
        type_key="BinType",
        type_value_map={
            "Burgundy 140L (refuse bin)": wt.GENERAL_WASTE,
            "Blue 240L (paper and cardboard bin)": wt.PAPER,
            "Grey 240L (glass, tins and plastics bin)": wt.RECYCLABLES,
            "Food Waste Caddy (External - large)": wt.FOOD_WASTE,
            "Food Waste Caddy (Internal - small)": wt.FOOD_WASTE,
        },
        carry_raw_label=True,
    )
