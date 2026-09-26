"""The 3C Shared Services waste calendar API (``servicelayer3c.azure-api.net``).

Cambridge City, South Cambridgeshire and Huntingdonshire run their bin-day
lookups on one shared API. A property is identified by its UPRN; the address
search turns a postcode into the UPRNs (and house numbers or names) at it::

    /wastecalendar/address/search/?postCode=CB13JD   -> [{id, houseNumber, ...}]
    /wastecalendar/collection/search/<uprn>/          -> {collections: [...]}

Each collection is a date plus the rounds run that day, e.g.
``{"date": "2026-09-04T00:00:00Z", "roundTypes": ["Refuse", "Food"]}``.
:class:`CollectionsParser` yields one ``(date, round)`` row per round. Cambridge
and South Cambridgeshire name their rounds ``DOMESTIC`` / ``RECYCLE`` /
``ORGANIC``, Huntingdonshire ``Refuse`` / ``Recycling`` / ``Garden`` / ``Food``;
``TYPE_VALUE_MAP`` covers both.
"""

from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from waste_collection_schedule import date_parsers, response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import HttpGetRetriever, TwoStepRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API = "https://servicelayer3c.azure-api.net/wastecalendar"

TYPE_VALUE_MAP = {
    "DOMESTIC": wt.GENERAL_WASTE,
    "RECYCLE": wt.RECYCLABLES,
    "ORGANIC": wt.ORGANIC,
    "Refuse": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden": wt.GARDEN_WASTE,
    "Food": wt.FOOD_WASTE,
}

PARSE_DATE = date_parsers.for_format("%Y-%m-%dT%H:%M:%SZ")


def uprn_retriever(
    uprn: str = "uprn", *, authority: "str | None" = None, take: int = 20
) -> HttpGetRetriever:
    """The collections of a property given by its UPRN."""

    def _params(**params: Any) -> "dict[str, Any]":
        query: dict[str, Any] = {"take": take}
        if authority is not None:
            query["authority"] = authority
        return query

    return HttpGetRetriever(
        url=lambda **params: f"{API}/collection/search/{params[uprn]}",
        params=_params,
    )


def address_retriever(
    postcode: str = "post_code", house: str = "number"
) -> TwoStepRetriever:
    """The collections of a property given by postcode and house number or name."""

    def _pick(lookup: Any, source: "BaseSource") -> str:
        code = source.params[postcode]
        # An unknown postcode is answered 400, an empty one with no addresses.
        if lookup.status_code == 400:
            raise SourceArgumentNotFound(postcode, code)
        lookup.raise_for_status()
        addresses = lookup.json()
        if not addresses:
            raise SourceArgumentNotFound(postcode, code)
        wanted = str(source.params[house]).strip().casefold()
        for address in addresses:
            if str(address.get("houseNumber", "")).strip().casefold() == wanted:
                return str(address["id"])
        raise SourceArgumentNotFoundWithSuggestions(
            house,
            source.params[house],
            [address.get("houseNumber") for address in addresses],
        )

    return TwoStepRetriever(
        lookup_url=lambda **params: (
            f"{API}/address/search/?"
            + urlencode({"postCode": str(params[postcode]).strip()})
        ),
        extract=_pick,
        schedule_url=lambda key, **_: f"{API}/collection/search/{key}/",
    )


class CollectionsParser(Parser["list[tuple[str, str]]"]):
    """One ``(date, round)`` row per round of each collection."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[str, str]]":
        response.raise_for_status()
        collections = response.json().get("collections")
        response_shape.expect(
            isinstance(collections, list),
            source_name=response_shape.source_name(source),
            detail="waste calendar reply has no collections list",
            raw=response.text,
        )
        return [
            (collection["date"], round_type)
            for collection in collections or []
            for round_type in collection.get("roundTypes") or []
        ]
