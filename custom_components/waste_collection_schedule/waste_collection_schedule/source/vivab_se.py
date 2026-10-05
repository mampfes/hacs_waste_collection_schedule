import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentSuggestionsExceptionBase,
)
from waste_collection_schedule.service.EdpFutureWeb import (
    TYPE_VALUE_MAP,
    EdpFutureWebParser,
    EdpFutureWebRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

API_URLS = {
    "falkenberg": "https://minasidor.vivab.info/FutureWebFalken/SimpleWastePickup/",
    "varberg": "https://minasidor.vivab.info/FutureWebVarberg/SimpleWastePickup/",
}

# Localities (tätorter) within each municipality served by VIVAB.
# Used to resolve a street_address to the correct regional API.
MUNICIPALITY_LOCALITIES = {
    "varberg": [
        "varberg",
        "bua",
        "kungsäter",
        "rolfstorp",
        "skällinge",
        "stråvalla",
        "träslövsläge",
        "tvååker",
        "veddige",
        "väröbacka",
        "åskloster",
        "åsa",
    ],
    "falkenberg": [
        "falkenberg",
        "glommen",
        "långås",
        "skogstorp",
        "slöinge",
        "ullared",
        "vessigebro",
        "ätran",
        "älvsered",
    ],
}


def _api_url(street_address=None, building_id=None, **_) -> str:
    """The deployment of the municipality the address's locality is in."""
    text = (street_address or "").lower()
    for municipality, localities in MUNICIPALITY_LOCALITIES.items():
        if any(re.search(rf"\b{re.escape(loc)}\b", text) for loc in localities):
            return API_URLS[municipality]
    if building_id:
        raise SourceArgumentSuggestionsExceptionBase(
            "street_address",
            "street_address should be 'Varberg' or 'Falkenberg' if using with "
            "building_id",
            ["Varberg", "Falkenberg"],
        )
    raise SourceArgumentException(
        "street_address",
        "Address not supported, should end with a locality within the Varberg or "
        "Falkenberg municipality (e.g. 'Varberg', 'Veddige', 'Tvååker', "
        "'Falkenberg', 'Ullared', 'Vessigebro')",
    )


@final
class Source(BaseSource):
    TITLE = "VIVAB Sophämtning"
    DESCRIPTION = "Source for VIVAB waste collection."
    URL = "https://www.vivab.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.FOOD_WASTE, wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Varberg: Gallerian": {"street_address": "Västra Vallgatan 2, Varberg"},
        "Varberg: Polisen": {"street_address": "Östra Långgatan 5, Varberg"},
        "Falkenberg: Storgatan 1": {"street_address": "Storgatan 1, FALKENBERG"},
        "Falkenberg: Östergränd 4": {"street_address": "Östergränd 4, Falkenberg"},
        "Storgtan 26, Falkenberg 1": {
            "street_address": "Falkenberg",
            "building_id": "0012165858",
        },
        "Storgtan 26, Falkenberg  2": {
            "street_address": "Falkenberg",
            "building_id": "9593062021",
        },
    }

    # Storgatan 26 in Falkenberg is two buildings the search lists under the
    # same address; the building id tells them apart.
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Storgtan 26, Falkenberg": {"street_address": "Storgatan 26, Falkenberg"},
        "Outside VIVAB": {"street_address": "Storgatan 1, Göteborg"},
    }

    PARAMS = (
        street_address("street_address"),
        text_field("building_id", "Building ID", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address ending in its locality (e.g. 'Östergränd "
            "4, Falkenberg'). Where several buildings share the address, give "
            "'building_id' (the number in brackets in the provider's search) and "
            "just 'Varberg' or 'Falkenberg' as the address."
        ),
    }

    retrieve = EdpFutureWebRetriever(
        _api_url,
        building_id="building_id",
        search_text=lambda street_address, **_: street_address.split(",")[0].strip(),
        exact_match=True,
    )
    parse = EdpFutureWebParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        carry_raw_label=True,
    )
