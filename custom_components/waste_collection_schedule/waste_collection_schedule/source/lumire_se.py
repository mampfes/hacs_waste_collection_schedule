from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://lumire.se/api/waste-pickup"


def _pick_building(response, *keys, address, **_) -> str:
    """The search answers ``{"addresses": [{address, buildingId}]}``; take the first."""
    addresses = response.json().get("addresses") or []
    if not addresses or not addresses[0].get("buildingId"):
        raise SourceArgumentNotFound("address", address)
    return str(addresses[0]["buildingId"])


def _waste_type(item) -> str:
    return (item.get("fee") or {}).get("waste_type") or item.get("description", "")


@final
class Source(BaseSource):
    TITLE = "Luleå"
    DESCRIPTION = "Source for Luleå."
    URL = "https://www.lumire.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PLASTIC,
        wt.PAPER,
        wt.METAL,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ringgatan 20": {"address": "Ringgatan 20"},
        "Gårdsvägen 11": {"address": "GÅRDSVÄGEN 11, LULEÅ"},
        "Ymergatan 5": {"address": "Ymergatan 5"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street address and house number as found by the address "
            "search at https://www.lumire.se/ (for example, Ringgatan 20)."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                API_URL,
                params=lambda address, **_: {"q": address},
                headers={"User-Agent": "Mozilla/5.0"},
                pick=_pick_building,
            ),
        ),
        url=lambda building_id, **_: f"{API_URL}/{building_id}",
        headers={"User-Agent": "Mozilla/5.0"},
    )

    parse = parsers.JsonParser("data")

    transform = JsonTransformer(
        date_key="nextPickup",
        type_key=_waste_type,
        skip_unparseable_dates=True,
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Plastförp.": wt.PLASTIC,
            "Pappersförp.": wt.PAPER,
            "Tidningar": wt.PAPER,
            "Wellpapp": wt.PAPER,
            "Metallförp.": wt.METAL,
            "Glasförp.ofärg": wt.GLASS,
            "Glasförp.färg": wt.GLASS,
            "Papper/Matavf.": [wt.PAPER, wt.FOOD_WASTE],
            "Restavf./Plast": [wt.GENERAL_WASTE, wt.PLASTIC],
        },
    )
