from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://api-universal.appbolaget.se/waste/addresses"
_HEADERS = {
    "Module": "universal",
    "Accept": "application/json, text/plain, */*",
    "Unit": "dd905ce7-b16d-4422-be36-564169af4035",
}


def _building_id(response, *, street_address: str, **_) -> str:
    """The first building the address search returns."""
    buildings = response.json()["data"]
    if not buildings:
        raise SourceArgumentNotFound("street_address", street_address)
    return buildings[0]["uuid"]


@final
class Source(BaseSource):
    TITLE = "Kristianstad Renhållning"
    DESCRIPTION = "Source for Kristianstad Renhållning waste collection."
    URL = "https://renhallningen-kristianstad.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Case_0": {"street_address": "Östra Boulevarden 1"},
        "Case_1": {"street_address": "Grenadjärvägen 1"},
        "Case_2": {"street_address": "Skogsvägen 18"},
        "Case_3": {"street_address": "Önnestadsvägen 7"},
    }

    PARAMS = (street_address("street_address"),)

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{_API_URL}/search",
                params=lambda street_address, **_: {"query": street_address},
                headers=_HEADERS,
                pick=_building_id,
            ),
        ),
        url=lambda building_id, **_: f"{_API_URL}/{building_id}",
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser("data", "services")
    # A four-compartment bin ("Fyrfack") is one service per bin, each holding
    # four fractions (renhallningen-kristianstad.se, "Fyrfackskärl").
    transform = JsonTransformer(
        date_key=lambda record: record["collection_at"][:10],
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        carry_raw_label=True,
        type_value_map={
            "Kärl 1": [wt.GENERAL_WASTE, wt.FOOD_WASTE, wt.GLASS, wt.PAPER],
            "Kärl 2": [wt.RECYCLABLES, wt.PAPER, wt.GLASS],
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Metallförp": wt.RECYCLABLES,
            "Plastförp": wt.RECYCLABLES,
            "Pappersförp": wt.PAPER,
            "Tidningar": wt.PAPER,
            "Färgat Glas": wt.GLASS,
            "Ofärgat Glas": wt.GLASS,
            "Trädgårdsavfall": wt.GARDEN_WASTE,
        },
    )
