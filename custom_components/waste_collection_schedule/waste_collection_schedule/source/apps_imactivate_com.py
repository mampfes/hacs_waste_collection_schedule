from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://bins.azurewebsites.net/api/"


def _norm_town(value: Any) -> str:
    return str(value).lower().replace(" ", "")


def _norm_street(value: Any) -> str:
    return str(value).lower().replace(" ", "").replace("road", "rd")


def _norm_number(value: Any) -> str:
    return str(value).lower().replace(" ", "").replace("\u0000", "")


def _postcode(response: Any, *keys: Any, postcode: Any, **_: Any) -> str:
    """The provider's own spelling of the postcode."""
    locations = response.json()
    if not locations:
        raise SourceArgumentNotFound("postcode", str(postcode))
    return str(locations[0]["Postcode"])


def _premise(
    response: Any, *keys: Any, town: Any, street: Any, number: Any, **_: Any
) -> tuple[int, str]:
    """``(premise id, local authority)`` of the address the user named."""
    data = response.json()
    wanted_town = _norm_town(town)
    wanted_street = _norm_street(street)
    wanted_number = _norm_number(number)

    street_matches = [
        location
        for location in data
        if _norm_street(location["Street"]) == wanted_street
        and _norm_town(location["Town"]) == wanted_town
    ]
    if not street_matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "street",
            f"{wanted_street}, {wanted_town}",
            suggestions={
                location["Street"]
                for location in data
                if _norm_town(location["Town"]) == wanted_town
            },
        )

    for location in street_matches:
        address1 = location["Address1"].strip()
        address2 = location["Address2"].strip()
        if wanted_number in (
            _norm_number(address1 + address2),
            _norm_number(address2 + address1),
        ):
            return location["PremiseID"], location["LocalAuthority"]

    raise SourceArgumentNotFoundWithSuggestions(
        "number",
        wanted_number,
        suggestions={
            _norm_number(location["Address1"] + location["Address2"])
            for location in street_matches
        },
    )


@final
class Source(BaseSource):
    TITLE = "Apps by imactivate"
    DESCRIPTION = "Source for Apps by imactivate."
    URL = "https://imactivate.com/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    REGIONS = (
        region("Leeds", url="https://www.leeds.gov.uk", town="Leeds"),
        region("Fenland", url="https://www.fenland.gov.uk"),
        region("Rotherham", url="https://www.rotherham.gov.uk", town="Rotherham"),
        region("Luton", url="https://www.luton.gov.uk", town="Luton"),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Leeds: LS6 2SE Leeds sharp mews 2": {
            "postcode": "LS62SE",
            "town": "Leeds",
            "street": "sharp mews",
            "number": 2,
        },
        "Fenland: PE15 8RD March 90 Creek Rd": {
            "postcode": "PE158RD",
            "town": "March",
            "street": "Creek Road",
            "number": "90",
        },
        "Rotherham: S61 4BH 2 Eskdale Rd, Rotherham": {
            "postcode": "S614BH",
            "town": "Rotherham",
            "street": "Eskdale Road",
            "number": 2,
        },
        "Luton: LU2 9DF 23 Marshall Rd": {
            "postcode": "LU2 9DF",
            "town": "Luton",
            "street": "Marshall Rd",
            "number": 23,
        },
    }

    PARAMS = (
        address(
            street_field="street",
            number="number",
            postcode_field="postcode",
            city_field="town",
        ),
    )

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API_URL}getlocation",
                params=lambda postcode, **_: {"postcode": postcode},
                pick=_postcode,
            ),
            retrievers.Lookup(
                f"{API_URL}getaddress",
                params=lambda real_postcode, **_: {"postcode": real_postcode},
                pick=_premise,
            ),
        ),
        url=f"{API_URL}getcollections",
        params=lambda real_postcode, premise, **_: {
            "premisesid": premise[0],
            "localauthority": premise[1],
        },
        raise_for_status=True,
    )
    parse = JsonParser()
    transform = JsonTransformer(
        date_key="CollectionDate",
        type_key="BinType",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "waste": wt.GENERAL_WASTE,
            "black": wt.GENERAL_WASTE,
            "pink bin": wt.GENERAL_WASTE,
            "residual": wt.GENERAL_WASTE,
            "glass": wt.GLASS,
            "garden": wt.GARDEN_WASTE,
            "food caddy": wt.FOOD_WASTE,
            "brown": wt.ORGANIC,
            "recycling": wt.RECYCLABLES,
            "green": wt.RECYCLABLES,
            "black bin": wt.RECYCLABLES,
            "green bin": wt.PAPER,
        },
    )
