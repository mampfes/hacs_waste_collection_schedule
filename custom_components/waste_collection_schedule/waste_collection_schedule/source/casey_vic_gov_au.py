import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    ExplodeList,
    RequireRecords,
    SelectExactMatch,
)
from waste_collection_schedule.transformers import JsonTransformer

SEARCH_PAGE_URL = "https://www.casey.vic.gov.au/find-your-bin-collection-day"
API_URL = "https://www.casey.vic.gov.au/coc-properties/api/search-address"

# Collection dates arrive as one property per bin and per direction, e.g.
# "NextGarbageDate" and "PreviousRecycleDate" (also spelt "Prev..."). The bin
# name is whatever sits between the two, so a new bin needs no mapping here --
# Glass appeared that way. Anchoring the whole key keeps a bin whose own name
# contains "Date" or "Next" intact.
_COLLECTION_DATE_KEY_RE = re.compile(r"^(?:Next|Prev(?:ious)?)(?P<name>.+)Date$")


def _search_params(street_address, **_):
    return {
        "term": street_address,
        "status": "C,F",
        "land_area": 0,
        "types": "",
        "inclusion": 0,
        "prop_type_details": "",
        "separate_address": 0,
        "bin_collection_details": "true",
    }


def _bin_dates(record, _source):
    """One ``{"date", "bin"}`` row per dated ``Next*Date``/``Prev*Date`` field."""
    rows = []
    for key, value in record.items():
        match = _COLLECTION_DATE_KEY_RE.match(key)
        if match and value:
            rows.append({"date": value, "bin": match.group("name")})
    return rows


@final
class Source(BaseSource):
    TITLE = "City of Casey"
    DESCRIPTION = "Source for the City of Casey rubbish collection."
    URL = "https://www.casey.vic.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    TEST_CASES: ClassVar[dict] = {
        "Butlers Kitchen": {
            "street_address": "55 Victor Crescent NARRE WARREN VIC 3805"
        },
        "Daniel's Donuts Cranbourne": {
            "street_address": "Shop 14/1085 South Gippsland Highway CRANBOURNE NORTH VIC 3977"
        },
    }
    PARAMS = (street_address("street_address"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            f'Visit the City of Casey "Find your bin collection day" page ({SEARCH_PAGE_URL}) '
            "and search for your address. Enter the full street address exactly as the "
            "autocomplete shows it, without commas and with the suburb and state in "
            "capitals, e.g. 55 Victor Crescent NARRE WARREN VIC 3805. Since the v3 "
            "pipeline migration, waste types use canonical, localised names. Update "
            "filters, automations and customisations using the old labels."
        ),
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.GLASS,
    ]

    # The search page is loaded first: it sets the session cookies the
    # autocomplete API expects.
    retrieve = retrievers.Request(
        API_URL,
        params=lambda _page, **params: _search_params(**params),
        before=(retrievers.Lookup(SEARCH_PAGE_URL, pick=lambda response, **_: None),),
    )
    parse = parsers.JsonParser("result")
    # The search matches substrings, so "8 Example Road ..." also returns 58,
    # 78, 88 and 148: the exact address is selected among them.
    preprocess = Compose(
        RequireRecords(
            argument="street_address",
            hint=f"The address returned no results. Check it on {SEARCH_PAGE_URL}",
        ),
        SelectExactMatch(
            argument="street_address", key=lambda record: record.get("full_address")
        ),
        ExplodeList(_bin_dates),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="bin",
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycle": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
            "Glass": wt.GLASS,
        },
    )
