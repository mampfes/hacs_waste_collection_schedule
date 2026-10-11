"""Sammelkalender.ch collection calendars, Swiss waste associations.

Several Swiss waste associations (Zeba, ZKRI, Real Luzern, ZAKU, the Nidwalden
association behind SUIBR) run the same "Sammelkalender" web application, each on its
own host. It has two JSON endpoints, a *search* and a *collections* one::

    GET <search>?optGem=GEM                      -> [{"GEMid", "GEMname"}, ...]
    GET <search>?optGem=<gem>&fuerStr=1          -> streets: [{"STRname", "STRhausnr", "SAGEid"}]
    GET <search>?optGem=<gem>&fuerSage=1         -> collection areas ("Sammelgebiete"):
                                                    [{"SAGEid", "SAGEname", "SAGEabk"}]
    GET <collections>?nGem=<gem>&nSage=<area>&jahr1=<year>&...
                                                 -> [{"DATUM": "2026-10-14", "AbarOne": "Kehricht-Grüngut"}]

A municipality is either divided by street (and, for long streets, house-number
range) or into collection areas; the street list is empty or a single placeholder
for the latter. ``AbarOne`` joins the waste types collected that day with ``-``.

:func:`calendar_retriever` walks that (municipality, then street and house number,
else the collection area, then the year's calendar, and next year's in December),
:func:`split_types` splits ``AbarOne`` and :func:`same` is the comparison the lookups
use. A source is its two URLs and the map from the type names to waste types.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.retrievers import Chain, Lookup, Request, YearlyRetriever

_LOGGER = logging.getLogger(__name__)


def same(first: Any, second: Any) -> bool:
    """Whether two names are the same address part: case, spaces and "Str."/"strasse" aside."""
    if first is None or second is None:
        return False

    def norm(text: Any) -> str:
        return (
            str(text)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("str.", "straße")
            .replace("strasse", "straße")
        )

    return norm(first) == norm(second)


def _municipality_id(response, *_, municipality, **__) -> str:
    municipalities = response.json()
    for item in municipalities:
        if same(item["GEMname"], municipality):
            return item["GEMid"]
    raise SourceArgumentNotFoundWithSuggestions(
        "municipality", municipality, [m["GEMname"] for m in municipalities]
    )


def _street_area(response, municipality_id, *_, street=None, hnr=None, **__):
    """The collection area id of the street and house number, or ``None`` when the
    municipality is divided into collection areas instead of streets."""
    streets = response.json()
    if not streets or (
        len(streets) == 1
        and streets[0].get("STRname") is None
        and streets[0].get("SAGEid") is not None
    ):
        return None

    names = sorted({s.get("STRname") or s.get("SAGEname") for s in streets} - {None})
    if len(streets) == 1:
        matches = streets
    else:
        if not street:
            raise SourceArgumentRequiredWithSuggestions(
                "street", "Street required for this municipality", names
            )
        matches = [s for s in streets if same(s.get("STRname"), street)]
        if not matches:
            raise SourceArgumentNotFoundWithSuggestions("street", street, names)

    for item in matches:
        if not item["STRhausnr"]:
            return item["SAGEid"]
        if hnr is None:
            raise SourceArgumentRequiredWithSuggestions(
                "hnr",
                "House number required for this street",
                [s["STRhausnr"] for s in matches],
            )
        if same(item["STRhausnr"], hnr):
            return item["SAGEid"]
    raise SourceArgumentNotFoundWithSuggestions(
        "hnr", str(hnr), sorted({s["STRhausnr"] for s in matches})
    )


def _collection_area(response, municipality_id, street_area, *_, street=None, **__):
    """The id of the collection area ("Sammelgebiet") the street field names."""
    areas = response.json()
    if not areas:
        return None
    if len(areas) == 1:
        return areas[0]["SAGEid"]
    if not street:
        # Existing configurations may have no street, because it was not
        # mandatory before: use the first area and say so.
        _LOGGER.warning(
            "No Sammelgebiet configured for this municipality. Using default "
            "Sammelgebiet '%s'. To configure, set 'street' to one of: %s",
            areas[0]["SAGEname"],
            ", ".join(sorted({a["SAGEname"] for a in areas})),
        )
        return areas[0]["SAGEid"]
    for area in areas:
        if same(street, area["SAGEabk"]) or same(street, area["SAGEname"]):
            return area["SAGEid"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, sorted({a["SAGEname"] for a in areas})
    )


def calendar_retriever(
    search_url: str | Callable[..., str], collections_url: str | Callable[..., str]
) -> YearlyRetriever:
    """The calendar of the ``municipality`` (and ``street``, ``hnr``) params.

    Both URLs may be callables of the params, for a source serving several hosts.
    """
    return YearlyRetriever(
        prepare=Chain(
            Lookup(
                search_url,
                params={"optGem": "GEM"},
                pick=_municipality_id,
            ),
            Lookup(
                search_url,
                params=lambda municipality_id, **_: {
                    "optGem": municipality_id,
                    "fuerStr": 1,
                },
                pick=_street_area,
            ),
            Lookup(
                search_url,
                params=lambda municipality_id, street_area, **_: {
                    "optGem": municipality_id,
                    "fuerSage": 1,
                },
                when=lambda municipality_id, street_area, **_: street_area is None,
                pick=_collection_area,
            ),
        ),
        fetch=Request(
            collections_url,
            params=lambda year, ids, **_: {
                "nGem": ids[0],
                "nAbar": "null",
                "nSage": ids[2] or ids[1],
                "sDatum": "",
                "delsel": "no",
                "jahr1": year,
            },
        ),
    )


def split_types(record: dict[str, Any], source: Any = None) -> list[str]:
    """The waste types of one day, ``AbarOne`` ("Kehricht-Grüngut") split at the dash."""
    return [part for part in (record.get("AbarOne") or "").split("-") if part]
