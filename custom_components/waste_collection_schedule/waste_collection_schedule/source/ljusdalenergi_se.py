import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.transformers import JsonTransformer

# Backend of the "Hämtningsdagar" page (garbage-collection-day.js).
_API = "https://hamtningsdagar.ljusdalenergi.se:3443/api/Address"
_PAGE = (
    "https://ljusdalenergi.se/renhallning/privatpersoner/sophamtning/"
    "nar-hamtas-dina-sopor/hamtningsdagar.html"
)

_TYPE_MAP: dict = {
    "Hushållsavfall": wt.GENERAL_WASTE,
    "Matavfall": wt.FOOD_WASTE,
    "Papper": wt.PAPER,
    "Tidningar": wt.PAPER,
    "Metall": wt.METAL,
    "Plast": wt.PLASTIC,
    "Färgat glas": wt.GLASS,
    "Ofärgat glas": wt.GLASS,
}


def _type_id(container_type: str) -> str:
    """Canonical type id, so e.g. coloured and clear glass on one day count once."""
    waste_type = _TYPE_MAP.get(container_type)
    return waste_type.id if waste_type else container_type


_HOUSE_LETTER = re.compile(r"(\d)\s+([a-zåäö])\b", re.IGNORECASE)


def _street(address: str) -> str:
    """The street and house number part of the address, house letter collapsed ("20 A" -> "20A")."""
    street = " ".join(address.partition(",")[0].split())
    return _HOUSE_LETTER.sub(r"\1\2", street)


def _city(address: str) -> str:
    """The town after the comma, without a postcode, casefolded ("" if none given)."""
    city = re.sub(r"\d", "", address.partition(",")[2])
    return " ".join(city.split()).casefold()


def _label(hit: dict) -> str:
    return f"{hit['StreetName'].strip()}, {hit['CityName'].strip().title()}"


def _service_ids(response, *_, address: str, **__) -> list:
    """All ServiceIds of the configured address.

    One address can carry several ServiceIds (e.g. one for household and food
    waste, another for the packaging bins), so every exact match is kept.
    """
    hits = response.json() or []
    if not hits:
        raise SourceArgumentNotFound("address", address)
    street, city = _street(address).casefold(), _city(address)
    exact = [
        hit
        for hit in hits
        if _street(hit["StreetName"]).casefold() == street
        and (not city or " ".join(hit["CityName"].split()).casefold() == city)
    ]
    if not exact or len({_label(hit) for hit in exact}) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address",
            address,
            list(dict.fromkeys(_label(hit) for hit in (exact or hits))),
        )
    return [hit["ServiceId"] for hit in exact]


@final
class Source(BaseSource):
    TITLE = "Ljusdal Energi"
    DESCRIPTION = "Source for Ljusdal Energi waste collection, Sweden."
    URL = "https://ljusdalenergi.se"
    COUNTRY = "se"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@vBrolin"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.METAL,
        wt.PLASTIC,
        wt.GLASS,
    ]
    TEST_CASES: ClassVar[dict] = {
        "Norra Järnvägsgatan 21, Ljusdal": {
            "address": "Norra Järnvägsgatan 21, Ljusdal"
        },
        "Stationsgatan 1, Järvsö": {"address": "Stationsgatan 1, Järvsö"},
        "Stationsgatan 4, Ljusdal": {"address": "Stationsgatan 4, Ljusdal"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "Ogiltigvägen 999"},
        "Ambiguous address": {"address": "Kyrkogatan"},
    }
    PARAMS = (street_address("address"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address and town as shown in the address search "
            f"on the [Hämtningsdagar page]({_PAGE}), e.g. "
            "`Norra Järnvägsgatan 21, Ljusdal`. The town is optional unless "
            "the same address exists in several towns. Ljusdal Energi's "
            "backend only answers requests from Swedish internet connections."
        ),
    }

    # Address/Search -> every exactly matching ServiceId -> one
    # Address/CollectionDays request per ServiceId.
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            f"{_API}/Search",
            params=lambda *_, address, **__: {"query": _street(address)},
            pick=_service_ids,
        ),
        targets=lambda source, service_ids: service_ids,
        fetch=retrievers.Request(
            f"{_API}/CollectionDays",
            params=lambda service_id, service_ids, **_: {"serviceId": service_id},
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser())
    # One row per container, each with a list of ISO dates; an address with
    # several bins of one kind lists the same date once per bin.
    preprocess = preprocessors.Compose(
        preprocessors.ExplodeList("Dates", into="date"),
        preprocessors.Deduplicate(
            key=lambda row: (row["date"], _type_id(row["ContainerType"]))
        ),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="ContainerType",
        type_value_map=_TYPE_MAP,
    )
