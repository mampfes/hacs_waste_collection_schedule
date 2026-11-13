from datetime import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import Collection, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

# The council replaced the IntraMaps widget with its own address / bin-day
# JSON API. Each stream's next collection is a dated ``collectDate``; we
# return those dates only (no weekday-rule projection).

ADDRESS_URL = "https://www.wanneroo.wa.gov.au/spatial/addresslookup"
BINDAY_URL = "https://www.wanneroo.wa.gov.au/spatial/bindaylookup"
_JSON_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

_STREAMS = {
    "generalWaste": wt.GENERAL_WASTE,
    "recycleWaste": wt.RECYCLABLES,
    "greenWaste": wt.GARDEN_WASTE,
}


def _norm(value: Any) -> str:
    return " ".join(str(value).split()).casefold()


def _pick_map_id(response, *_, address, **__) -> str:
    """The mapId of the suggestion that matches the entered address."""
    suggestions = response.json()
    if not isinstance(suggestions, list):
        suggestions = []
    wanted = _norm(address)
    exact = [
        item
        for item in suggestions
        if isinstance(item, dict) and _norm(item.get("address")) == wanted
    ]
    labels = [
        str(item.get("address"))
        for item in suggestions
        if isinstance(item, dict) and item.get("address")
    ]
    if len(exact) == 1:
        return str(exact[0]["mapId"])
    if len(exact) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address", address, [str(item.get("address")) for item in exact]
        )
    raise SourceArgumentNotFoundWithSuggestions("address", address, labels)


def _classify(self, record: dict) -> list[Collection] | None:
    """One collection per stream that has a collectDate."""
    entries: list[Collection] = []
    for key, waste_type in _STREAMS.items():
        item = record.get(key) or {}
        raw = item.get("collectDate") if isinstance(item, dict) else None
        if not raw:
            continue
        try:
            collected = datetime.fromisoformat(str(raw)).date()
        except ValueError:
            continue
        entries.append(Collection(date=collected, waste_type=waste_type))
    return entries or None


@final
class Source(BaseSource):
    TITLE = "City of Wanneroo"
    DESCRIPTION = "Source for City of Wanneroo."
    URL = "https://www.wanneroo.wa.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "1 Atlanta DR TWO ROCKS": {"address": "1 Atlanta DR TWO ROCKS"},
        "13/26 Princeton CIR ALEXANDER HEIGHTS": {
            "address": "13/26 Princeton CIR ALEXANDER HEIGHTS"
        },
        "99 Two Rocks RD TWO ROCKS": {"address": "99 Two Rocks RD TWO ROCKS"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '1 Atlanta DR TWO ROCKS')."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                ADDRESS_URL,
                method="POST",
                json=lambda address, **_: {"address": address},
                headers=_JSON_HEADERS,
                pick=_pick_map_id,
            ),
        ),
        url=BINDAY_URL,
        method="POST",
        json=lambda map_id, **_: {"mapId": map_id},
        headers=_JSON_HEADERS,
    )
    parse = parsers.JsonParser()
    classify = _classify
