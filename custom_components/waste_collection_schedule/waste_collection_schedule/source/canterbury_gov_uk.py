from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import RowTransformer

ADDRESS_URL = "https://trsewmllv7.execute-api.eu-west-2.amazonaws.com/dev/address"
COLLECTION_URL = (
    "https://n6ljrw455m.execute-api.eu-west-2.amazonaws.com/prod/get-bin-dates"
)

# The API rejects requests that do not look like they come from the council site.
HEADERS = {
    "Origin": "https://www.canterbury.gov.uk",
    "Referer": "https://www.canterbury.gov.uk/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
}

_TYPE_MAP = {
    "blackBinDay": wt.GENERAL_WASTE,
    "recyclingBinDay": wt.RECYCLABLES,
    "foodBinDay": wt.FOOD_WASTE,
    "gardenBinDay": wt.GARDEN_WASTE,
}


def _house(lpi: dict) -> str | None:
    return lpi.get("PAO_TEXT") or lpi.get("PAO_START_NUMBER")


def _pick_property(response, *keys, post_code, number, **_) -> dict:
    """The address search answers ``{"results": [{"LPI": {...}}, ...]}``."""
    results = response.json().get("results") or []
    if not results:
        raise SourceArgumentNotFound("post_code", post_code)

    wanted = str(number).lower()
    lpis = [r["LPI"] for r in results]
    for lpi in lpis:
        if (
            str(lpi.get("PAO_TEXT") or "").lower() == wanted
            or str(lpi.get("PAO_START_NUMBER") or "").lower() == wanted
        ):
            return {"uprn": lpi["UPRN"], "usrn": lpi["USRN"]}

    raise SourceArgumentNotFoundWithSuggestions(
        "number", number, {h for lpi in lpis if (h := _house(lpi))}
    )


@final
class Source(BaseSource):
    TITLE = "Canterbury City Council"
    DESCRIPTION = "Source for canterbury.gov.uk services for canterbury"
    URL = "https://canterbury.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "houseNumber": {"post_code": "ct68ru", "number": "63"},
        "houseName": {"post_code": "ct68ru", "number": "KOWLOON"},
        "gardenWaste": {"post_code": "CT6 8RU", "number": "55"},
    }

    PARAMS = (
        postcode("post_code"),
        text_field("number", label="House Number or Name"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your house number, or your house name if "
            "it has no number."
        ),
    }

    retrieve = retrievers.Request(
        COLLECTION_URL,
        method="POST",
        before=(
            retrievers.Lookup(
                ADDRESS_URL,
                params=lambda post_code=None, **_: {
                    "postcode": post_code,
                    "type": "standard",
                },
                pick=_pick_property,
            ),
        ),
        json=lambda prop, **_: prop,
        headers=HEADERS,
    )

    parse = parsers.KeyedDateListsParser("dates", fields=_TYPE_MAP)

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map=_TYPE_MAP,
    )
