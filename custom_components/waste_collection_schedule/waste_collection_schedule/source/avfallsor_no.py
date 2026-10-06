import re
from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import Compose, ExplodeList, RowFilter
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://avfallsor.no/wp-json"

# The provider's own fraction names (Norwegian).
_TYPE_MAP = {
    "Restavfall": wt.GENERAL_WASTE,
    "Bioavfall": wt.ORGANIC,
    "Papp og papir": wt.PAPER,
    # Plastic packaging is a round of its own, so it maps to PLASTIC.
    "Plastemballasje": wt.PLASTIC,
    "Glassemballasje": wt.GLASS,
    "Metallemballasje": wt.METAL,
}


def _split_round(record, source) -> list:
    """One round collects glass and metal packaging together: one record each."""
    if record.get("fraksjon") == "Glass- og metallemballasje":
        return [
            {**record, "fraksjon": "Glassemballasje"},
            {**record, "fraksjon": "Metallemballasje"},
        ]
    return [record]


def _upcoming(record, source) -> bool:
    """The calendar also lists days already past; keep today and later."""
    return date.fromisoformat(str(record["dato"])[:10]) >= date.today()


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
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
        wt.GLASS,
        wt.METAL,
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

    preprocess = Compose(
        ExplodeList("items"), ExplodeList(_split_round), RowFilter(_upcoming)
    )

    transform = JsonTransformer(
        date_key="dato",
        type_key="fraksjon",
        type_value_map=_TYPE_MAP,
    )
