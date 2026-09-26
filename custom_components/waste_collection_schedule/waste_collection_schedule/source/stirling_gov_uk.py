import datetime
from typing import ClassVar, final
from urllib.parse import urlencode

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ReCollect import (
    TYPE_VALUE_MAP,
    ReCollectEventsParser,
)
from waste_collection_schedule.transformers import ICSTransformer

# Stirling Council uses Routeware's ReCollect platform (area "StirlingUK"). The
# address is resolved to a ReCollect place id through the area's own address
# search, then the shared ReCollect events parser reads the place's schedule.
# (recollect_net serves the same council for a user who already has the place id.)
_API_BASE = "https://api.eu.recollect.net/api"
_AREA_URL = f"{_API_BASE}/areas/StirlingUK/services/waste"


def _pick_place(lookup, source) -> str:
    """The ReCollect place id the configured address resolves to."""
    address = source.params["address"]
    lookup.raise_for_status()
    suggestions = lookup.json()

    if not suggestions:
        raise SourceArgumentNotFound("address", address)

    if len(suggestions) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address", address, [s["name"] for s in suggestions]
        )

    suggestion = suggestions[0]
    if suggestion.get("type") != "parcel" or "place_id" not in suggestion:
        # Multi-dwelling postcodes return a "place_qualifier" which needs a
        # more specific address to resolve to a single property.
        raise SourceArgumentNotFound(
            "address",
            address,
            "this looks like a multi-dwelling postcode, please add your house number or property name.",
        )
    return suggestion["place_id"]


def _events_url(place_id: str) -> str:
    today = datetime.date.today()
    query = urlencode(
        {
            "hide": "reminder_only",
            "after": (today - datetime.timedelta(days=30)).isoformat(),
            "before": (today + datetime.timedelta(days=365)).isoformat(),
            "locale": "en-GB",
        }
    )
    return f"{_API_BASE}/places/{place_id}/services/waste/events?{query}"


@final
class Source(BaseSource):
    TITLE = "Stirling Council"
    DESCRIPTION = "Source for Stirling Council waste collection services."
    URL = "https://www.stirling.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@nagug"]

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Kildean Road 38": {"address": "38 Kildean Road"},
        "Merlo Buchanan Castle Estate": {"address": "Merlo"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/ "
            "and type your address into the search to see the exact wording, then use "
            "the same here. House number and street (e.g. '38 Kildean Road'), property "
            "name (e.g. 'Merlo'), or a single-dwelling postcode work."
        ),
    }

    retrieve = retrievers.TwoStepRetriever(
        lookup_url=lambda address, **_: (
            f"{_AREA_URL}/address-suggest?"
            + urlencode({"q": address, "locale": "en-GB"})
        ),
        extract=_pick_place,
        schedule_url=lambda place_id, **_: _events_url(place_id),
    )
    parse = ReCollectEventsParser(place_id="address")
    transform = ICSTransformer(type_value_map=TYPE_VALUE_MAP)
