from typing import ClassVar, final

from waste_collection_schedule import date_parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://kundapi.affarsverken.se/api/v1/open-api"


def _token(response, *_keys, **_params) -> str:
    """The bearer token the login endpoint answers with."""
    return response.text.strip()


def _building_query(response, *_keys, address: str = "", **_params) -> str:
    """The query handle of the building the search matched (an exact match wins)."""
    results = [r for r in response.json() or [] if r.get("query")]
    wanted = address.strip().casefold()
    for result in results:
        if str(result.get("address", "")).strip().casefold() == wanted:
            return result["query"]
    if len(results) == 1:
        return results[0]["query"]
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [r.get("address") for r in results]
    )


def _bearer(token, *_args, **_params) -> dict:
    return {"Authorization": f"Bearer {token}"}


@final
class Source(BaseSource):
    TITLE = "Affärsverken"
    DESCRIPTION = "Source for Affärsverken."
    URL = "https://www.affarsverken.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": "Enter the address as the Affärsverken website writes it, street and number followed by the locality, e.g. `Albatrossvägen 5, Ramdala`.",
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Albatrossvägen 5, Ramdala": {"address": "Albatrossvägen 5, Ramdala"},
        "Sturkövägen 1, Sturkö": {"address": "Sturkövägen 1, Sturkö"},
        "Uddabygd 107, Rödeby": {"address": "Uddabygd 107, Rödeby"},
        "Zenitavägen 11, Hasslö": {"address": "Zenitavägen 11, Hasslö"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "Ingen gata 999"},
    }

    PARAMS = (street_address("address"),)

    retrieve = retrievers.Request(
        lambda token, query, **_: f"{API_URL}/waste/buildings/{query}",
        headers=_bearer,
        before=(
            retrievers.Lookup(
                f"{API_URL}/login",
                method="POST",
                params={"BrandName": "Affarsverken"},
                data="",
                pick=_token,
            ),
            retrievers.Lookup(
                f"{API_URL}/waste/buildings/search",
                params=lambda token, address, **_: {"address": address},
                headers=_bearer,
                pick=_building_query,
            ),
        ),
    )
    parse = JsonParser("services")

    transform = JsonTransformer(
        date_key="nextPickup",
        type_key="title",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        skip_unparseable_dates=True,
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Trädgårdsavfall": wt.GARDEN_WASTE,
            "Hemkompost": wt.ORGANIC,
            # Four-compartment bin for packaging and newspapers.
            "Fyrfack 1": wt.RECYCLABLES,
            "Fyrfack 2": wt.RECYCLABLES,
            "Metallförp.": wt.METAL,
            "Pappersförp.": wt.PAPER,
            "Tidningar": wt.PAPER,
            "Wellpapp": wt.CARTONS,
            "Glasförp.färg": wt.GLASS,
            "Glasförp.ofärg": wt.GLASS,
            "Plastförp.": wt.PLASTIC,
        },
        carry_raw_label=True,
    )
