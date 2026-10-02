import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://avfallsor.no/wp-json"

# The provider's own fraction names (Norwegian).
_TYPE_MAP = {
    "Restavfall": wt.GENERAL_WASTE,
    "Bioavfall": wt.FOOD_WASTE,
    "Papp og papir": wt.PAPER,
    "Plastemballasje": wt.RECYCLABLES,
    "Glassemballasje": wt.GLASS,
    # No canonical metal type: kept as OTHER, shown with the provider's label.
    "Metallemballasje": wt.OTHER,
}


def _split_round(record, source) -> list:
    """One round collects glass and metal packaging together: one record each."""
    if record.get("fraksjon") == "Glass- og metallemballasje":
        return [
            {**record, "fraksjon": "Glassemballasje"},
            {**record, "fraksjon": "Metallemballasje"},
        ]
    return [record]


def _normalize(text: str) -> str:
    return text.lower().replace(" ", "").replace(",", "").replace(".", "").casefold()


def _property_id(response, *keys, address, **_) -> str:
    """Pick the property id off the matching address's ``href``.

    The label includes the city ("Auglandslia 1, Kristiansand"), the value
    does not, so an address given with or without the city both match.
    """
    matches = response.json()
    wanted = _normalize(address)
    for match in matches:
        if wanted in (_normalize(match["label"]), _normalize(match.get("value", ""))):
            found = re.search(r"/([0-9a-f-]{36})/?$", match["href"])
            if not found:
                raise ValueError(
                    f"Could not extract propertyId from href: {match['href']}"
                )
            return found.group(1)
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [match["label"] for match in matches]
    )


@final
class Source(BaseSource):
    TITLE = "Avfall Sør, Kristiansand"
    DESCRIPTION = "Source for Avfall Sør, Kristiansand."
    URL = "https://avfallsor.no/"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Auglandslia 1, Kristiansand": {"address": "Auglandslia 1, Kristiansand"},
        "Auglandslia 1 (without city)": {"address": "Auglandslia 1"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as shown on [avfallsor.no](https://avfallsor.no/) "
            "(Finn hentedag), e.g. 'Auglandslia 1, Kristiansand'. The city may be "
            "left out."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{_API}/addresses/v1/address",
                # The API prefix-matches street and number; drop any city suffix.
                params=lambda address, **_: {
                    "lookup_term": address.split(",")[0].strip()
                },
                pick=_property_id,
            ),
        ),
        url=lambda property_id, **_: (
            f"{_API}/pickup-calendar/v1/collections/property-id/{property_id}"
        ),
    )

    parse = parsers.JsonParser("collections")

    preprocess = Compose(ExplodeList("items"), ExplodeList(_split_round))

    transform = JsonTransformer(
        date_key="dato",
        type_key="fraksjon",
        type_value_map=_TYPE_MAP,
        carry_raw_label=True,
    )
