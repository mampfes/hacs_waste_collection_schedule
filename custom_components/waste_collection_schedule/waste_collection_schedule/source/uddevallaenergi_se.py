import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://app.uddevallaenergi.se/wp-json/app"
_HEADERS = {
    "Accept": "application/json",
    "X-App-Identifier": "www.uddevallaenergi.se",
}

# Labels carry the bin volume in front, e.g. "370 l kärl 2".
_SIZE_PREFIX = re.compile(r"^\s*\d+\s*l\s+", re.IGNORECASE)


def _plant_number(response, *, street_address: str, **_) -> str:
    """The plant number of the hit whose address equals the configured one."""
    hits = [
        hit
        for hit in response.json()
        if not hit.get("is_key") and hit.get("address") and hit.get("plant_number")
    ]
    wanted = street_address.strip().casefold()
    for hit in hits:
        if hit["address"].strip().casefold() == wanted:
            return hit["plant_number"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_address", street_address, [hit["address"] for hit in hits]
    )


@final
class Source(BaseSource):
    TITLE = "Uddevalla Energi"
    DESCRIPTION = "Source for Uddevalla Energi waste collection schedules."
    URL = "https://www.uddevallaenergi.se/privat/sophamtning.html"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.OTHER]

    TEST_CASES: ClassVar[dict] = {
        "Fjällvägen 11, Ljungskile": {"street_address": "Fjällvägen 11, Ljungskile"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your address on the Uddevalla Energi waste collection "
            "webpage and enter it exactly as shown, including the town, e.g. "
            "`Fjällvägen 11, Ljungskile`."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API}/v2/address-flat",
                params=lambda street_address, **_: {
                    "address": street_address.split(",")[0]
                },
                headers=_HEADERS,
                pick=_plant_number,
            ),
        ),
        url=f"{_API}/v1/next-pickup-web",
        params=lambda plant_number, **_: {"plant_number": plant_number},
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser()
    # "Kärl 1" / "Kärl 2" are the two compartment bins of a multi-compartment
    # container; their contents are not published, so they stay OTHER with the
    # raw label kept as the description.
    transform = JsonTransformer(
        date_key="pickup_date",
        type_key="type",
        clean=lambda label: _SIZE_PREFIX.sub("", label),
        carry_raw_label=True,
        type_value_map={
            "kärl 1": wt.OTHER,
            "kärl 2": wt.OTHER,
        },
    )
