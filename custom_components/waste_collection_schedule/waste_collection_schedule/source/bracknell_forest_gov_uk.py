import json
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = (
    "https://selfservice.mybfc.bracknell-forest.gov.uk/w/webpage/waste-collection-days"
)
_PARAMS = {
    "webpage_subpage_id": "PAG0000570FEFFB1",
    "webpage_token": "390170046582b0e3d7ca68ef1d6b4829ccff0b1ae9c531047219c6f9b5295738",
    "widget_action": "handle_event",
}
_HEADERS = {
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",
}
_CELL = {
    "action_cell_id": "PCL0003988FEFFB1",
    "action_page_id": "PAG0000570FEFFB1",
}
_DATE = re.compile(r"\d{1,2} \w+ \d{4}")


def _event(action: str, **params) -> dict:
    """The widget event form: an action and its JSON-encoded parameters."""
    return {"code_action": action, "code_params": json.dumps(params)} | _CELL


def _address_id(response, *, post_code: str, house_number, **_) -> str:
    """The postcode's address that starts with the house number or name."""
    addresses = response.json()["response"]["addresses"]["items"]
    prefix = str(house_number).upper()
    if prefix.isnumeric():
        # "3 " so that 3 does not match 30 or 31.
        prefix = f"{prefix} "
    for address in addresses:
        if address["Description"].upper().startswith(prefix):
            return address["Id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number",
        house_number,
        [address["Description"] for address in addresses],
    )


def _date(sentence: str) -> str:
    """The date in "Your next food collection is Tuesday 29 September 2026"."""
    match = _DATE.search(sentence)
    return match.group(0) if match else ""


@final
class Source(BaseSource):
    TITLE = "Bracknell Forest Council"
    DESCRIPTION = "Bracknell Forest Council, UK - Waste Collection"
    URL = "https://selfservice.mybfc.bracknell-forest.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "44 Kennel Lane": {"house_number": "44", "post_code": "RG42 2HB"},
        "28 Kennel Lane": {"house_number": "28", "post_code": "RG42 2HB"},
        "32 Ashbourne": {"house_number": "32", "post_code": "RG12 8SG"},
        "1 Acacia Avenue": {"house_number": "1", "post_code": "GU47 0RU"},
        "Myrtle, 39 New Wokingham Road": {
            "house_number": "Myrtle",
            "post_code": "RG45 6JG",
        },
    }

    PARAMS = (postcode("post_code", "house_number"),)

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _API_URL,
                method="POST",
                params=_PARAMS,
                headers=_HEADERS,
                data=lambda post_code, **_: _event("find_addresses", search=post_code),
                pick=_address_id,
            ),
        ),
        url=_API_URL,
        method="POST",
        params=lambda address_id, **_: _PARAMS,
        headers=_HEADERS,
        data=lambda address_id, **_: _event("find_rounds", addressId=address_id),
        raise_for_status=True,
    )
    # Each round lists its next three collections as sentences.
    parse = parsers.JsonParser("response", "collections")
    preprocess = ExplodeList("upcomingCollections", into="sentence")
    transform = JsonTransformer(
        date_key=lambda collection: _date(collection["sentence"]),
        type_key="round",
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
        },
    )
