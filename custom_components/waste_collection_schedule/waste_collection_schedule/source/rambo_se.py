from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://rambo.se/wp-json/app/v1"
_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "X-App-Identifier": "www.rambo.se/hamtdag",
}


def _plant_number(response, *, address: str, **_) -> str:
    """The plant number of the hit whose address is the configured one."""
    hits = [hit for hit in response.json() if "address" in hit]
    wanted = address.strip().lower()
    for hit in hits:
        if hit["address"].strip().lower() == wanted:
            return hit["plant_number"].replace(" ", "+")
    if not hits:
        raise SourceArgumentNotFound(
            "address",
            address,
            "write it exactly as it is on the website",
        )
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [hit["address"] for hit in hits]
    )


@final
class Source(BaseSource):
    TITLE = "North / Middle Bohuslän - Rambo AB"
    DESCRIPTION = "Source for North / Middle Bohuslän - Rambo AB."
    URL = "https://www.rambo.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Grebbestad Ö.långgat./Storg., Grebbestad": {
            "address": "Grebbestad Ö.långgat./Storg., Grebbestad"
        },
        "Grebbestadsvägen 6, Tanumshede": {"address": "Grebbestadsvägen 6, Tanumshede"},
        "Torgvägen 1, Centrum, Hedekas": {"address": "Torgvägen 1, Centrum, Hedekas"},
        "Örekilsvägen Munkedals Reningsverk 10, Munkedal": {
            "address": "Örekilsvägen Munkedals Reningsverk 10, Munkedal"
        },
        "Storgatan 39, Smögen": {"address": "Storgatan 39, Smögen"},
    }

    PARAMS = (street_address(),)

    # The search takes the street part; the hit is matched on the whole
    # address, town included.
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{_API_URL}/address-flat",
                params=lambda address, **_: {"address": address.split(",")[0]},
                headers=_HEADERS,
                pick=_plant_number,
            ),
        ),
        url=f"{_API_URL}/next-pickup-web",
        params=lambda plant_number, **_: {"plant-number": plant_number},
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser("types")
    # The four-compartment bins each hold four fractions (rambo.se,
    # "Hemsortering").
    transform = JsonTransformer(
        date_key="pickup_date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        carry_raw_label=True,
        type_value_map={
            "Kärl 1": [wt.FOOD_WASTE, wt.GENERAL_WASTE, wt.PAPER, wt.RECYCLABLES],
            "Kärl 2": [wt.GLASS, wt.PAPER, wt.RECYCLABLES],
            "Restavfall": wt.GENERAL_WASTE,
            "Hushållsavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Kärl": wt.GENERAL_WASTE,
        },
    )
