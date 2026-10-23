"""ISL Fusion bin calendars (``<council>.isl-fusion.com``), Northern Ireland councils.

Fermanagh and Omagh and Lisburn and Castlereagh publish their bin days through the
same ISL Fusion portal, each on its own host. It has two JSON endpoints:

* ``GET /address/<postcode>`` answers ``{"html": "<ul><li><a href=\\"/view/<id>/\\">
  19A MARKET SQUARE, LISBURN. BT28 1AG</a></li>..."}``, the properties of the
  postcode and their ids;
* ``GET /calendar/<id>/<date>`` answers ``{"nextCollections": {"collections":
  {"2026-10-13": {"date": ..., "collections": {<id>: {"name": "Blue Recycling",
  ...}}}}}}``, the next collection day with every bin collected on it.

:func:`calendar_retriever` resolves the property (or takes its id directly) and
fetches the calendar; :class:`CollectionsParser` reads it into ``(date, bin name)``
rows. A council is its host, the map from its bin names to waste types and its
test addresses::

    retrieve = calendar_retriever("https://example.isl-fusion.com")
    parse = CollectionsParser()
"""

from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Lookup, Request

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(",", " ")).strip().upper()


def _property_id(
    response: Any, *_: Any, postcode: str, house_number: Any, **__: Any
) -> str:
    """The id of the property at the postcode whose address starts with the house number or name.

    ``19`` matches ``19 MARKET SQUARE`` but neither ``19A MARKET SQUARE`` nor
    ``119 MARKET SQUARE``.
    """
    try:
        html = response.json().get("html")
    except ValueError:
        html = None
    if not html:
        raise SourceArgumentNotFound("postcode", postcode)

    properties = {}
    for link in BeautifulSoup(html, "html.parser").select("li a[href]"):
        property_id = str(link["href"]).replace("/view", "").strip("/")
        properties[link.get_text(strip=True)] = property_id
    if not properties:
        raise SourceArgumentNotFound("postcode", postcode)

    wanted = _normalise(str(house_number))
    matches = {
        address: property_id
        for address, property_id in properties.items()
        if _normalise(address).startswith(wanted)
        and not _normalise(address)[len(wanted) :][:1].isalnum()
    }
    if len(matches) == 1:
        return next(iter(matches.values()))
    if matches:
        raise SourceArgAmbiguousWithSuggestions(
            "house_number", str(house_number), sorted(matches)
        )
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", str(house_number), sorted(properties)
    )


def calendar_retriever(base_url: str) -> Request:
    """The calendar of the ``property_id`` param, or of the property that
    ``postcode`` and ``house_number`` pick out."""
    return Request(
        lambda key, **_: f"{base_url}/calendar/{key}/{datetime.date.today():%Y-%m-%d}",
        before=(
            Lookup(
                lambda postcode, **_: f"{base_url}/address/{postcode}",
                given=lambda property_id=None, **_: property_id or None,
                pick=_property_id,
            ),
        ),
    )


class CollectionsParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, bin name)`` rows from the calendar's next collection days."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        days = ((response.json().get("nextCollections") or {}).get("collections")) or {}
        return [
            (datetime.date.fromisoformat(day["date"]), bin_["name"])
            for day in days.values()
            for bin_ in day["collections"].values()
        ]
