import datetime
import json
import re
from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import JsonTransformer

_BASE_URL = "https://www.vakin.se"
_PAGE_URL = (
    f"{_BASE_URL}/kundserviceochetjanster/sophamtning/"
    "narkommersopbilen.4.6252338c1a0c6bd088ed01f.html"
)

# The "När kommer sopbilen?" widget on the waste page is a Sitevision app
# (applicationId "se.soleil.garbageTruckFetcher"). The endpoints for address lookup
# and collection data are:
#   <BASE_URL>/appresource/<page_id>/<portlet_id>/getAddresses
#   <BASE_URL>/appresource/<page_id>/<portlet_id>/getcontainerdata
# Both ids are Sitevision-internal and reassigned whenever the page or widget
# placement is rebuilt, so they are extracted from the live page HTML.
_PORTLET_ID_PATTERN = re.compile(
    r"applicationId:\s*['\"]se\.soleil\.garbageTruckFetcher[^'\"]*['\"].*?"
    r"portletId:\s*['\"]([^'\"]+)['\"]"
)
_PAGE_ID_PATTERN = re.compile(r"pageId:\s*['\"]([^'\"]+)['\"]")
_HOUSE_LETTER = re.compile(r"(\d+)\s+([A-Za-zÅÄÖåäö])\b")
_POSTCODE = re.compile(r",?\s*\b\d{3}\s?\d{2}\b$")


class _WidgetEndpoints(NamedTuple):
    """The dynamic page and portlet identifiers discovered from the schedule page."""

    page_id: str
    portlet_id: str


def _pick_widget_endpoints(response, **_) -> _WidgetEndpoints:
    """Extract Sitevision page and portlet identifiers from the schedule page HTML."""
    html = response.text
    page_match = _PAGE_ID_PATTERN.search(html)
    portlet_match = _PORTLET_ID_PATTERN.search(html)
    if not page_match or not portlet_match:
        raise ValueError(
            "Could not locate the garbageTruckFetcher widget on the Vakin website; "
            "the page layout may have changed."
        )
    return _WidgetEndpoints(page_match.group(1), portlet_match.group(1))


def _clean_address_query(address: str) -> str:
    """Clean the input address for search by collapsing house letters and stripping postal codes."""
    stripped = _POSTCODE.sub("", address).strip()
    return _HOUSE_LETTER.sub(r"\1\2", stripped)


def _normalise(a: str) -> str:
    """Normalise an address for comparison (collapsed house letter, no postal code, casefold)."""
    return _clean_address_query(a).casefold()


def _pick_address(response, _endpoint: _WidgetEndpoints, *, address: str, **_) -> dict:
    """Find the matching address object from the /getAddresses search results."""
    data = response.json() if hasattr(response, "json") else json.loads(response.text)
    items = data.get("data", []) if isinstance(data, dict) else []

    if not items:
        raise SourceArgumentNotFound("address", address)

    if len(items) == 1:
        return items[0]["value"]

    # Try exact match against label or address field (normalised on both sides)
    wanted = _normalise(address)
    for item in items:
        label = _normalise(str(item.get("label", "")))
        val_addr = _normalise(str(item.get("value", {}).get("address", "")))
        if wanted in (label, val_addr):
            return item["value"]

    suggestions = [item.get("label", "") for item in items[:10] if item.get("label")]
    raise SourceArgAmbiguousWithSuggestions("address", address, suggestions)


def _schedule_params(address_val: dict) -> dict[str, str]:
    """Request a rolling 365-day schedule window starting today."""
    today = datetime.date.today()
    start_date = today.isoformat()
    end_date = (today + datetime.timedelta(days=365)).isoformat()
    return {
        "addressParams": json.dumps(address_val),
        "startDate": start_date,
        "endDate": end_date,
    }


@final
class Source(BaseSource):
    TITLE = "Vakin"
    DESCRIPTION = (
        "Waste collection schedule for Vakin (Umeå, Nordmaling, and Vindeln), Sweden."
    )
    URL = _BASE_URL
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.PLASTIC,
        wt.OTHER,
    ]

    REGIONS = (
        region("Umeå", url="https://www.vakin.se"),
        region("Nordmaling", url="https://www.vakin.se"),
        region("Vindeln", url="https://www.vakin.se"),
    )

    TEST_CASES: ClassVar[dict] = {
        "Kajakvägen 3, Täfteå": {"address": "Kajakvägen 3, Täfteå"},
        "Storgatan 1 A, Umeå": {"address": "Storgatan 1 A, Umeå"},
        "Storgatan 101, Umeå": {"address": "Storgatan 101, Umeå"},
        "Vindelvägen 1, Hällnäs": {"address": "Vindelvägen 1, Hällnäs"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "Ogiltigvägen 99999"},
        "Ambiguous address": {"address": "Storgatan 1"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street name and house number, followed by the town if "
            "needed (e.g. `Kajakvägen 3, Täfteå` or `Storgatan 101, Umeå`), as "
            f"shown in the address search on the [Vakin waste page]({_PAGE_URL})."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _PAGE_URL,
                pick=_pick_widget_endpoints,
            ),
            retrievers.Lookup(
                url=lambda endpoint, **_: (
                    f"{_BASE_URL}/appresource/{endpoint.page_id}/"
                    f"{endpoint.portlet_id}/getAddresses"
                ),
                params=lambda endpoint, address, **_: {
                    "pickupAddress": _clean_address_query(address)
                },
                pick=_pick_address,
            ),
        ),
        url=lambda endpoint, address_val, **_: (
            f"{_BASE_URL}/appresource/{endpoint.page_id}/"
            f"{endpoint.portlet_id}/getcontainerdata"
        ),
        params=lambda endpoint, address_val, **_: _schedule_params(address_val),
        raise_for_status=True,
    )

    parse = parsers.JsonParser()

    preprocess = preprocessors.ExplodeList("contentTypes", into="waste_type")

    transform = JsonTransformer(
        date_key="executionDate",
        type_key="waste_type",
        type_value_map={
            "Matavfall": wt.FOOD_WASTE,
            "Restavfall": wt.GENERAL_WASTE,
            "Pappersförpackningar": wt.PAPER,
            "Plastförpackningar": wt.PLASTIC,
            "Fett": wt.OTHER,
        },
    )
