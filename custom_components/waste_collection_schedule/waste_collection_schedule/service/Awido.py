"""Cubefour AWIDO platform (DE).

AWIDO hosts the waste calendars of dozens of German districts and towns under
one web service, one ``client`` id per customer. An address narrows one level at
a time, each level answering a ``[{"key": ..., "value": ...}]`` list::

    getPlaces/client=<client>            -> places (municipalities)
    getGroupedStreets/<place>            -> streets of a place
    getStreetAddons/<street>             -> house numbers of a street (optional)
    getData/<key>                        -> the calendar for the narrowest key

``steps()`` declares those levels for ``retrievers.LookupChainRetriever`` and
``DATA_URL`` / ``data_params`` the calendar request, so a source only names its
parameters. ``AwidoParser`` flattens the ``getData`` document.

Some clients have no street level at all (the place is the whole address), and
some streets have no house numbers; both resolve to the next-narrower key.
"""

import logging
from collections.abc import Iterable
from typing import Any

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Lookup

_LOGGER = logging.getLogger(__name__)

API = "https://awido.cubefour.de/WebServices/Awido.Service.svc/secure"


def _norm(value: Any) -> str:
    return str(value).strip().lower()


def _match(argument: str, wanted: Any, options: Iterable[dict]) -> Any:
    """The key of the option whose label equals ``wanted`` (case and edge space ignored)."""
    keyed = {_norm(option["value"]): option["key"] for option in options}
    found = keyed.get(_norm(wanted))
    if found is None:
        raise SourceArgumentNotFoundWithSuggestions(argument, wanted, list(keyed))
    return found


def _pick_place(response, *_, city, **__):
    return _match("city", city, response.json())


def _pick_street(response, place, *_, street=None, **__):
    streets = response.json()
    if street is None:
        # No street given: the place doubles as its only street (a client
        # without a street level lists one entry carrying the place's calendar).
        return streets[0]["key"] if streets else place
    return _match("street", street, streets)


def _pick_house_number(response, place, street_key, *_, housenumber, **__):
    options = response.json()
    numbers = [_norm(option["value"]) for option in options]
    if not numbers or numbers == [""]:
        _LOGGER.warning("No housenumbers found for street, using street only")
        return street_key
    return _match("housenumber", housenumber, options)


def steps(customer: str = "customer") -> tuple[Lookup, ...]:
    """The place, street and house-number lookups of one AWIDO client."""
    return (
        Lookup(
            lambda *_, **params: f"{API}/getPlaces/client={params[customer].lower()}",
            pick=_pick_place,
        ),
        Lookup(
            lambda place, **_: f"{API}/getGroupedStreets/{place}",
            params=lambda *_, **params: {"client": params[customer].lower()},
            pick=_pick_street,
        ),
        Lookup(
            lambda place, street_key, **_: f"{API}/getStreetAddons/{street_key}",
            params=lambda *_, **params: {"client": params[customer].lower()},
            # No street or no house number given: the street key is the answer.
            given=lambda place, street_key, *, street=None, housenumber=None, **_: (
                street_key if street is None or housenumber is None else None
            ),
            pick=_pick_house_number,
        ),
    )


def data_url(place, street_key, address_key, **_) -> str:
    return f"{API}/getData/{address_key}"


def data_params(*_, customer, **__) -> dict:
    return {"fractions": "", "client": customer.lower()}


class AwidoParser(Parser["list[dict[str, Any]]"]):
    """Flatten a ``getData`` document into one record per dated collection.

    ``calendar`` lists days. A day with collections carries parallel lists: ``fr``
    the fraction codes and ``ad`` the address each applies to. Days without
    ``ad`` are public holidays. A fraction code is named in ``fracts``.

    Each record is ``{"date": "YYYYMMDD", "type": <fraction name>,
    "description": <address or None>}``.
    """

    def __call__(self, response, source=None) -> "list[dict[str, Any]]":
        data = response.json()
        names = {fraction["snm"]: fraction["nm"] for fraction in data["fracts"]}
        records: list[dict[str, Any]] = []
        for day in data["calendar"]:
            if day["ad"] is None:
                continue
            addresses = day.get("ad") or []
            for index, code in enumerate(day.get("fr") or []):
                address = addresses[index] if index < len(addresses) else None
                records.append(
                    {
                        "date": day["dt"],
                        "type": names[code],
                        "description": address or None,
                    }
                )
        return records
