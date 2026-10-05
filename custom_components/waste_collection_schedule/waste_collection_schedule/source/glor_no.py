from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import EachResponse, JsonParser
from waste_collection_schedule.preprocessors import Deduplicate
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.transformers import JsonTransformer

_SEARCH_URL = "https://proaktiv.glor.offcenit.no/search"
_DETAILS_URL = "https://proaktiv.glor.offcenit.no/details"


def _normalize(value: str) -> str:
    return "".join(value.casefold().replace(".", "").replace(",", "").split())


def _street_part(address: str) -> str:
    """The street + house number, before the optional municipality."""
    return address.split(",")[0].strip()


def _properties(response, *keys, address, **_) -> list[str]:
    """The ids of every property listed at the address.

    The municipality may follow the street after a comma ("Storgata 1,
    Lillehammer"). The search only matches the street part, so that is what it
    is queried with, and the municipality narrows the matches afterwards.
    """
    matches = response.json()
    street_norm = _normalize(_street_part(address))
    candidates = [m for m in matches if _normalize(m["adresse"]) == street_norm]

    if "," in address:
        kommune_norm = _normalize(address.split(",", 1)[1])
        candidates = [m for m in candidates if _normalize(m["kommune"]) == kommune_norm]
    elif len({m["kommune"] for m in candidates}) > 1:
        # The same street exists in more than one municipality served by GLØR:
        # the user has to add the municipality after a comma.
        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            address,
            sorted({f"{m['adresse']}, {m['kommune']}" for m in candidates}),
        )

    if not candidates:
        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            address,
            sorted({f"{m['adresse']}, {m['kommune']}" for m in matches}),
        )
    return [m["id"] for m in candidates]


@final
class Source(BaseSource):
    TITLE = "GLØR"
    DESCRIPTION = (
        "Source for GLØR (Gudbrandsdal Lillehammer Øyer Ringebu Renovasjon), Norway."
    )
    URL = "https://glor.no"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Storgata 1, Lillehammer": {"address": "Storgata 1, Lillehammer"},
        "Segalstadsetervegen 33, Gausdal": {
            "address": "Segalstadsetervegen 33, Gausdal"
        },
        "Gudbrandsdalsvegen 187 (without city)": {"address": "Gudbrandsdalsvegen 187"},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your address at glor.no/tømmeplan. Use the address "
            "exactly as shown in the result list, optionally followed by the "
            "municipality name, for example 'Storgata 1, Lillehammer'."
        ),
    }

    PARAMS = (street_address(),)

    # A street address can list several properties (one per unit); every one's
    # schedule is fetched, and identical rows are merged below.
    retrieve = FanOutRetriever(
        prepare=Lookup(
            _SEARCH_URL,
            params=lambda address, **_: {"q": _street_part(address)},
            pick=_properties,
        ),
        targets=lambda source, ids: ids,
        fetch=Request(_DETAILS_URL, params=lambda id, ids, **_: {"id": id}),
    )
    parse = EachResponse(JsonParser())
    preprocess = Deduplicate(key=lambda item: (item["dato"][:10], item["fraksjon"]))
    transform = JsonTransformer(
        date_key=lambda item: item["dato"][:10],
        type_key="fraksjon",
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Papir, papp": wt.PAPER,
            "Plast blandet": wt.RECYCLABLES,
            "Matavfall": wt.FOOD_WASTE,
            "Hermetikk- og glassemballasje": wt.GLASS,
        },
    )
