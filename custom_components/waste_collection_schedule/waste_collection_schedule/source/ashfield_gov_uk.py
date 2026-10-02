from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    postcode,
    text_field,
    uprn,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

API = "https://www.ashfield.gov.uk/api/address"

_TYPE_MAP = {
    "Residual Waste Collection Service": wt.GENERAL_WASTE,
    "Domestic Recycling Collection Service": wt.RECYCLABLES,
    "Domestic Glass Collection Service": wt.GLASS,
    "Garden Waste Collection Service": wt.GARDEN_WASTE,
}


def _pick_uprn(response, *keys, post_code, number=None, name=None, **_) -> str:
    """The address search answers ``{"results": [{"DPA": {...}}, ...]}``."""
    addresses = response.json()["results"]
    if not addresses:
        raise SourceArgumentNotFound("post_code", post_code)

    dpas = [x.get("DPA") or {} for x in addresses]
    if name:
        wanted = name.casefold()
        matching = [
            d for d in dpas if (d.get("BUILDING_NAME") or "").casefold() == wanted
        ]
    else:
        matching = [d for d in dpas if d.get("BUILDING_NUMBER") == str(number)]

    for dpa in matching:
        if dpa.get("UPRN"):
            return str(int(dpa["UPRN"]))

    raise SourceArgumentNotFoundWithSuggestions(
        "name" if name else "number",
        name or number,
        [
            f"{d.get('BUILDING_NUMBER', '')} {d.get('BUILDING_NAME', '')}".strip()
            for d in dpas
        ],
    )


@final
class Source(BaseSource):
    TITLE = "Ashfield District Council"
    DESCRIPTION = "Source for ashfield.gov.uk, Ashfield District Council, UK"
    URL = "https://www.ashfield.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "11 Maun View Gardens, Sutton-in-Ashfield": {"uprn": 10001336299},
        "101 Main Street, Huthwaite": {"uprn": "100031253415"},
        "1 Acacia Avenue, Kirkby-in-Ashfield": {"post_code": "NG17 9BH", "number": "1"},
        "Council Offices, Kirkby-in-Ashfield": {
            "post_code": "NG178ZA",
            "name": "COUNCIL OFFICES",
        },
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [postcode("post_code"), house_number("number")],
            [postcode("post_code"), text_field("name", "House name")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter either your UPRN (available from "
            "[FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)) OR your "
            "postcode and either your house number (`number`) or your building "
            "name (`name`)."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda post_code=None, **_: f"{API}/search/{post_code}",
                given=lambda uprn=None, **_: uprn,
                pick=_pick_uprn,
            ),
        ),
        url=lambda key, **_: f"{API}/collections/{int(key)}",
    )

    parse = parsers.JsonParser("collections")

    transform = JsonTransformer(
        date_key="date",
        type_key="service",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
    )
