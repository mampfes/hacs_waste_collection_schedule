import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

_FIND_URL = "https://www.fenland.gov.uk/find"


def _pick_address(response, post_code=None, house_number=None, **_) -> tuple:
    """Postcode search -> (uprn, lat, lng) of the first address starting with the house number."""
    addresses = response.json()
    if not addresses:
        raise SourceArgumentNotFound("post_code", post_code)
    # House numbers are not separated from the address line.
    wanted = re.compile(rf"^{re.escape(str(house_number).strip())} ", re.IGNORECASE)
    for address in addresses:
        if wanted.search(address["line1"]):
            return address["udprn"], address["latitude"], address["longitude"]
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number",
        house_number,
        list(dict.fromkeys(a["line1"].split(" ")[0] for a in addresses)),
    )


@final
class Source(BaseSource):
    TITLE = "Fenland District Council"
    DESCRIPTION = "Source script for fenland.gov.uk services for Fenland"
    URL = "https://www.fenland.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Address1": {"post_code": "PE13 1JR", "house_number": "Flat 1"},
        "Address2": {"post_code": "PE15 0SD", "house_number": 1},
    }

    PARAMS = (postcode("post_code", "house_number"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and the house number (or flat or house name) as "
            "it starts your address, e.g. `Flat 1` for `Flat 1 24 North Brink`."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
    ]

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _FIND_URL,
                params=lambda post_code=None, **_: {
                    "type": "postcodesearch",
                    "postcode": post_code,
                },
                headers={"Accept": "application/json"},
                pick=_pick_address,
            ),
        ),
        url=_FIND_URL,
        params=lambda address, **_: {
            "type": "loadlayer",
            "layerId": 2,
            "uprn": address[0],
            "lat": address[1],
            "lng": address[2],
        },
        headers={"Accept": "application/json"},
    )

    parse = parsers.JsonParser("features", 0, "properties", "upcoming")

    preprocess = preprocessors.ExplodeList("collections")

    # collectionDate is an instant (23:00Z is midnight of the next day in BST).
    transform = JsonTransformer(
        date_key="collectionDate",
        type_key="name",
        parse_date=date_parsers.in_timezone("Europe/London"),
        type_value_map={
            "Empty Bin FOOD CADDY": wt.FOOD_WASTE,
            "Empty Bin GREEN 240": wt.GENERAL_WASTE,
            "Empty Bin REFUSE SACK": wt.GENERAL_WASTE,
            "Empty Bin BLUE 240": wt.RECYCLABLES,
            "Empty Bin RECYCLING SACK": wt.RECYCLABLES,
            "Empty Bin BROWN 240": wt.ORGANIC,
        },
    )
