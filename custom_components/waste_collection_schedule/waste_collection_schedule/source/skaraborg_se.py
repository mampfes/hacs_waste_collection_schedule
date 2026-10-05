from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

API = "https://gullspang.avfallsapp.se/api/nova/v1/next-pickup"

# The public client credentials shipped inside the Avfallsapp mobile app.
_HEADERS = {
    "Authorization": "Bearer J6lD4hVH8pRMQZeBSoCvtCZj1V0wvgg0QvBqSDTH9fce942d",
    "X-App-Identifier": "70bae483-3268-4875-93f5-14f2274ec7cb",
}


def _plant_id(response, address: str, city: str, **_) -> str:
    """The plant number of the search hit matching both address and city."""
    results = response.json()
    if not results:
        raise SourceArgumentNotFound("address", address)
    hits = results.get(city, [])
    for hit in hits:
        if hit["zip_city"] == city and hit["address"] == address:
            return hit["plant_number"]
    if not hits:
        raise SourceArgumentNotFoundWithSuggestions("city", city, list(results))
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [hit["address"] for hit in hits]
    )


@final
class Source(BaseSource):
    TITLE = "Avfall & Återvinning Skaraborg"
    DESCRIPTION = "Source for Skaraborg."
    URL = "https://avfallskaraborg.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.FOOD_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Granängsvägen 1, Skövde": {"address": "Granängsvägen 1", "city": "Skövde"},
        "Skaraborgs tingsrätt": {"address": "Eric Ugglas Plats 2", "city": "Skövde"},
    }

    PARAMS = (street_address("address"), city("city"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address and city exactly as they appear when you "
            "search for your address on https://avfallskaraborg.se/."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{API}/search",
                params=lambda address, **_: {"address": address},
                headers=_HEADERS,
                pick=_plant_id,
            ),
        ),
        url=f"{API}/address",
        method="POST",
        data=lambda plant_id, **_: {"plant_id": plant_id},
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser("bins")
    transform = JsonTransformer(
        date_key="pickup_date",
        type_key="type",
        type_value_map={
            "Brännbart": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Plast/Kartong": wt.RECYCLABLES,
            "Färgat glas/Ofärgat glas": wt.GLASS,
        },
    )
