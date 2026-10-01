from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

# The council's official bin-collection lookup page
# (https://www.cityofsydney.nsw.gov.au/waste-recycling-services/find-my-bin-collection-day)
# embeds a widget hosted on this domain, which in turn proxies the council's
# own "lga/property" API. This is the same endpoint the official page uses.
API_BASE = "https://cos-bin-collection-widget.netlify.app/api"


def _pick_property(response: Any, *keys: Any, address: str, **_: Any) -> int:
    """Resolve the typed address to the property key of its single/exact match."""
    matches = response.json().get("matchingProperties") or []
    if not matches:
        raise SourceArgumentNotFound("address", address)
    if len(matches) == 1:
        return int(matches[0]["propertyKey"])
    normalized = address.strip().lower()
    for match in matches:
        if match["fullAddress"].strip().lower() == normalized:
            return int(match["propertyKey"])
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [match["fullAddress"] for match in matches]
    )


def _bins(response: Any, source: Any = None) -> list:
    """The ``bins`` list; a 204 means no schedule exists for the property."""
    if response.status_code == 204:
        return []
    response.raise_for_status()
    return response.json().get("bins") or []


@final
class Source(BaseSource):
    TITLE = "City of Sydney"
    DESCRIPTION = "Source for City of Sydney (NSW) bin collection."
    URL = "https://www.cityofsydney.nsw.gov.au"
    COUNTRY = "au"
    SOURCE_CODEOWNERS: ClassVar[list] = []
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "17 Junction Street, Forest Lodge": {
            "address": "17 Junction Street, Forest Lodge",
        },
        "216 Chalmers Street, Redfern": {
            "address": "216 Chalmers Street, Redfern",
        },
    }

    PARAMS = (street_address("address"),)

    WASTE_TYPES = (wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb (e.g. '17 Junction "
            "Street, Forest Lodge'), as it would appear on the council's "
            "[find my bin collection day]"
            "(https://www.cityofsydney.nsw.gov.au/waste-recycling-services/find-my-bin-collection-day) "
            "page."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{API_BASE}/search",
                params=lambda address, **_: {"address": address},
                headers={"Accept": "application/json"},
                pick=_pick_property,
            ),
        ),
        url=lambda key, **_: f"{API_BASE}/property/{key}/bins-collection",
        headers={"Accept": "application/json"},
    )

    parse = staticmethod(_bins)

    preprocess = ExplodeList("nextPickupDate", "pickupDateAfterNext", into="date")

    transform = JsonTransformer(
        date_key="date",
        type_key="roundDescription",
        type_value_map={
            "Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green Waste": wt.GARDEN_WASTE,
            "Food Scraps": wt.FOOD_WASTE,
        },
        parse_date=date_parsers.for_format("%A %d/%m/%Y"),
    )
