from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import Deduplicate
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://www.vasyd.se/api/sitecore/MyPagesApi"


def _building(response, *keys, street_address, **_) -> str:
    """The id of the first building the address search finds."""
    buildings = response.json()["items"]
    if not buildings:
        raise SourceArgumentNotFound("street_address", street_address)
    return buildings[0]["id"]


@final
class Source(BaseSource):
    TITLE = "VA Syd Sophämntning"
    DESCRIPTION = "Source for VA Syd waste collection."
    URL = "https://www.vasyd.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Home": {"street_address": "Industrigatan 13, Arlöv"},
        "Storgatan": {"street_address": "Storgatan 1, Malmö"},
        "Kungsgatan": {"street_address": "Kungsgatan 10, Malmö"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the address as VA Syd lists it: '<street> <number>, <city>', for "
            "example 'Storgatan 1, Malmö'. The first address the search finds is "
            "used, so include the city to avoid a wrong match."
        ),
        "de": (
            "Geben Sie die Adresse so ein, wie VA Syd sie führt: '<Straße> "
            "<Nummer>, <Ort>', zum Beispiel 'Storgatan 1, Malmö'. Es wird der erste "
            "Treffer der Suche verwendet, geben Sie daher den Ort mit an."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API_URL}/BuildingAddressSearch",
                method="POST",
                data=lambda street_address, **_: {"query": street_address},
                pick=_building,
            ),
        ),
        url=f"{_API_URL}/WastePickupByAddress",
        method="POST",
        data=lambda building, street_address, **_: {
            "query": building,
            "street": street_address,
        },
    )
    parse = JsonParser("items")
    # An address with several bins of one kind lists the collection once each.
    preprocess = Deduplicate(
        key=lambda item: (item["nextWastePickup"], item["wasteType"])
    )
    transform = JsonTransformer(
        date_key="nextWastePickup",
        type_key="wasteType",
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Trädgårdsavfall": wt.GARDEN_WASTE,
            # Used cooking fat and oil collected in its own bin.
            "Fett": wt.OTHER,
        },
    )
