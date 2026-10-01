from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    location_id,
    street_address,
)
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.preprocessors import Deduplicate
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://www.hedemoraenergi.se/wp-json/internal/v1/fetchplanner"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HomeAssistant-WCS/1.0)"}


def _suggestion(result: dict) -> str:
    address = result["address"]
    if result.get("city") and result.get("zipCode"):
        return f"{address}, {result['zipCode']} {result['city']}"
    if result.get("city"):
        return f"{address}, {result['city']}"
    return address


def _pickup_id(response, *_, address: str | None = None, **__) -> str:
    """The pickup id of the single address hit; several hits are ambiguous."""
    data = response.json()
    if data.get("success") is not True:
        raise ValueError("Unexpected response from Hedemora Energi search API")
    results = data.get("results") or []
    if not results:
        raise SourceArgumentNotFound("address", address)
    if len(results) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address",
            address,
            [_suggestion(r) for r in results if r.get("address")],
        )
    return results[0]["id"]


@final
class Source(BaseSource):
    TITLE = "Hedemora Energi"
    DESCRIPTION = "Source for Hedemora Energi waste collection schedules, Sweden."
    URL = "https://www.hedemoraenergi.se/"
    COUNTRY = "se"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@crazyboy89"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Åsgatan 28": {"address": "Åsgatan 28"},
        "Pickup ID 1392000": {"pickup_id": "1392000"},
    }

    PARAMS = (
        alternatives(
            [location_id("pickup_id")],
            [street_address("address")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use `pickup_id` if known. Otherwise enter the exact address as "
            "shown in Hedemora Energi's fetch planner search."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API}/search",
                method="POST",
                params=lambda *_, address=None, **__: {"address": address},
                headers=_HEADERS,
                given=lambda *_, pickup_id=None, **__: pickup_id,
                pick=_pickup_id,
            ),
        ),
        url=f"{_API}/calendar",
        params=lambda resolved, **_: {"pickup_id": resolved},
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser("data")
    # A property with several containers of one kind lists each pickup per container.
    preprocess = Deduplicate(key=lambda job: (job["ExecutionDate"], job["ContentType"]))
    transform = JsonTransformer(
        date_key="ExecutionDate",
        type_key="ContentType",
        type_value_map={
            "Brännbart": wt.GENERAL_WASTE,
            "Restavfall": wt.GENERAL_WASTE,
            "Kompost": wt.ORGANIC,
            "Matavfall": wt.FOOD_WASTE,
            "Papper": wt.PAPER,
            "Plast": wt.RECYCLABLES,
        },
    )
