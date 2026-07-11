"""NSR - Nordvästra Skånes Renhållnings AB (nsr.se).

Demonstrates: an address-search lookup (optionally filtered by a trailing
", City") feeding an ICS-download request, via ``TwoStepRetriever``. The feed
itself duplicates every event, so ``parse`` is a source-defined override that
de-duplicates after conversion.
"""

from typing import ClassVar, final
from urllib.parse import urlencode

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://nsr.se/api/wastecalendar"


def _split(full_address: str) -> tuple[str, str]:
    """Split "Street 1, City" into street and optional city filter."""
    if "," in full_address:
        street, city_filter = (p.strip() for p in full_address.split(",", maxsplit=1))
        return street, city_filter
    return full_address, ""


def _pick_address_id(lookup, source) -> str:
    full_address = source.params["address"]
    street, city_filter = _split(full_address)

    results = lookup.json().get("fp", [])
    if not results:
        raise SourceArgumentNotFound("address", full_address)

    if city_filter:
        filtered = [
            e for e in results if e.get("Ort", "").lower() == city_filter.lower()
        ]
        if filtered:
            results = filtered

    match = next(
        (e for e in results if e.get("Adress", "").lower() == street.lower()), None
    )
    if match is not None:
        return match["id"]
    if len(results) == 1:
        return results[0]["id"]

    suggestions = [f"{e['Adress']}, {e['Ort']}" for e in results if "Adress" in e]
    raise SourceArgumentNotFoundWithSuggestions("address", full_address, suggestions)


def _schedule_url(address_id: str, address: str, **_) -> str:
    street, _city_filter = _split(address)
    query = urlencode(
        {
            "query": street,
            "id": address_id,
            "calendar_type": "ical",
            "action": "fetchDataFromFetchPlannerCalendar",
            "level": "ajax",
            "type": "json",
        }
    )
    return f"{_API_URL}/calendar?{query}"


@final
class Source(BaseSource):
    TITLE = "NSR - Nordvästra Skånes Renhållnings AB"
    DESCRIPTION = "Source for NSR waste collection schedule in northwest Skåne, Sweden."
    URL = "https://nsr.se"
    COUNTRY = "se"

    TEST_CASES: ClassVar[dict] = {
        "Kattarp villa": {"address": "Signestorpsvägen 1"},
        "Helsingborg city": {"address": "Drottninggatan 100, Helsingborg"},
        "Kattarp with garden waste": {"address": "Signestorpsvägen 13"},
    }

    REGIONS = (
        region(
            "NSR Tömningskalender",
            url="https://nsr.se/privat/allt-om-din-sophamtning/nar-toms-mitt-karl/tomningskalender/",
            country="se",
        ),
    )

    PARAMS = (text_field("address", label="Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as shown on the NSR website (e.g. "
            "'Storgatan 1'). Do not include postal code. Search at "
            "https://nsr.se/privat/allt-om-din-sophamtning/nar-toms-mitt-karl/tomningskalender/"
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = TwoStepRetriever(
        lookup_url=lambda address, **_: (
            f"{_API_URL}/search?{urlencode({'query': _split(address)[0]})}"
        ),
        extract=_pick_address_id,
        schedule_url=_schedule_url,
    )

    def parse(self, response, source=None):
        seen: set = set()
        entries = []
        for entry in ICS().convert(response.text):
            if entry in seen:
                continue
            seen.add(entry)
            entries.append(entry)
        return entries

    transform = ICSTransformer(
        type_value_map={
            "KÄRL 1": GENERAL_WASTE,
            "KÄRL 2": RECYCLABLES,
            "Trädgårdsavfall": GARDEN_WASTE,
            "Restavfall": GENERAL_WASTE,
            "Matavfall": FOOD_WASTE,
            "Pappersförpackningar": PAPER,
            "Tidningar": PAPER,
            "Ofärgat glas": GLASS,
            "Färgat glas": GLASS,
            "Plastförpackningar": RECYCLABLES,
            "Metallförpackningar": RECYCLABLES,
            "Miljöfarligt avfall": HAZARDOUS,
        }
    )

    def __init__(self, address: str):
        super().__init__(address=address)
