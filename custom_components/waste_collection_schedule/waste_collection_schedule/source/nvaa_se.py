from typing import ClassVar, final

from waste_collection_schedule import date_parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://sjalvservice.nvaa.se/api/v1/integration"


def _building_id(response, *_keys, street_address: str = "", **_params) -> str:
    """The id of the address the search matched (an exact match wins)."""
    results = response.json().get("results") or []
    wanted = street_address.strip().casefold()
    for result in results:
        if str(result.get("address", "")).strip().casefold() == wanted and result.get(
            "id"
        ):
            return result["id"]
    for result in results:
        if result.get("id"):
            return result["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_address", street_address, [r.get("address") for r in results]
    )


@final
class Source(BaseSource):
    TITLE = "Norrtälje Vatten & Avfall"
    DESCRIPTION = (
        "Source for Norrtälje Vatten & Avfall waste collection services, Sweden."
    )
    URL = "https://sjalvservice.nvaa.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": "Enter the address as the self-service site writes it, street and number followed by the locality, e.g. `Hamndalsvägen 2, Norrtälje`.",
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.FOOD_WASTE, wt.OTHER]

    TEST_CASES: ClassVar[dict] = {
        "Hamndalsvägen 2, Norrtälje": {"street_address": "Hamndalsvägen 2, Norrtälje"},
        "Rödhakestigen 1, Väddö": {"street_address": "Rödhakestigen 1, Väddö"},
    }

    PARAMS = (street_address("street_address"),)

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API_URL}/findAddress",
                method="POST",
                data=lambda street_address, **_: {"address": street_address},
                pick=_building_id,
            ),
        ),
        url=f"{API_URL}/getNextGarbageCollection",
        method="POST",
        data=lambda building_id, **_: {"buildingId": building_id},
    )

    transform = JsonTransformer(
        date_key="next_collection",
        type_key="product",
        parse_date=date_parsers.first_of(
            date_parsers.named_month(), date_parsers.iso_week()
        ),
        skip_unparseable_dates=True,
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            # Septic/sludge emptying has no canonical type.
            "Slam": wt.OTHER,
        },
        carry_raw_label=True,
    )
