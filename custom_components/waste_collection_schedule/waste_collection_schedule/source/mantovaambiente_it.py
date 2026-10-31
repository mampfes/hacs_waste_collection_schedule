"""Mantova Ambiente (Gruppo TEA), Italy.

The provider's website runs on the BEdita 3 CMS, whose public REST API serves
the collection calendars:

- ``/api/zones`` lists every collection zone as ``{"id", "title"}``. The title
  is the municipality's name, followed by the zone's label where the
  municipality is split into several zones ("Gonzaga Zona 1", "Mantova
  quartieri Zona 1", "Marmirolo frazioni", "Settimo Milanese Zona A - Sud").
- ``/api/objects/<zone>/relations/recycling_event_place`` pages through the
  zone's collection events, at most 100 per page, oldest first, with no sort or
  date filter. Each event is titled "<zone> - <waste>" and carries its dates in
  ``date_items``, already expanded from the recurrence rule with its exceptions
  removed.

Composes: :class:`~waste_collection_schedule.retrievers.FanOutRetriever`.
``prepare`` resolves the configured municipality and zone against the zone list,
then reads the number of pages from a one-item request; each page is one
target. A zone without a published calendar answers ``"data": []`` with no
paging, which is reported against the argument that selected it.

The same date and waste type can come from two events (a one-off collection
added beside the recurring series), so the rows are deduplicated.
"""

import math
import re
from typing import Any, ClassVar, TypedDict, final

from waste_collection_schedule import (
    date_parsers,
    field_terms,
    parsers,
    regions,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.preprocessors import Compose, Deduplicate, ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://www.mantovaambiente.it/api"
PAGE_SIZE = 100  # the API's maximum page size
TIMEOUT = 120  # the API is slow: a full page can take close to a minute

# "<municipality> <zone label>", the label being "Zona 1", "Zona A - Sud",
# "quartieri Zona 1", "centro Zona B", "comune" or "frazioni".
_ZONE_TITLE = re.compile(
    r"^(?P<municipality>.+?)\s+(?:(?:quartieri|centro)\s+)?(?:zona\b.*|comune|frazioni)$",
    re.IGNORECASE,
)


class _DateItem(TypedDict):
    start_date: str


class _Event(TypedDict):
    title: str
    date_items: list[_DateItem]


def _normalise(value: str) -> str:
    """Casefold, unify apostrophes and collapse whitespace.

    The API writes "Castel d'Ario" with a straight apostrophe, the website with a
    typographic one.
    """
    for char in "’‘´`":
        value = value.replace(char, "'")
    return " ".join(value.split()).casefold()


def _municipality_of(zone_title: str) -> str:
    match = _ZONE_TITLE.match(zone_title.strip())
    return match.group("municipality") if match else zone_title.strip()


def _zone_id(response, comune: str, zona: str | None = None, **_) -> str:
    """The id of the configured zone, read from ``/api/zones``."""
    by_municipality: dict[str, list[dict[str, Any]]] = {}
    for zone in response.json()["data"]:
        by_municipality.setdefault(_municipality_of(zone["title"]), []).append(zone)

    wanted = _normalise(comune)
    names = [name for name in by_municipality if _normalise(name) == wanted]
    if not names:
        names = [
            name
            for name in by_municipality
            if _normalise(name).split()[: len(wanted.split())] == wanted.split()
        ]
    if not names:
        raise SourceArgumentNotFoundWithSuggestions(
            "comune", comune, sorted(by_municipality, key=str.casefold)
        )
    if len(names) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "comune", comune, sorted(names, key=str.casefold)
        )

    name = names[0]
    zones = by_municipality[name]
    labels = {
        str(zone["id"]): zone["title"].strip()[len(name) :].strip() for zone in zones
    }
    suggestions = sorted(label for label in labels.values() if label)

    if not zona:
        if len(zones) == 1:
            return str(zones[0]["id"])
        raise SourceArgumentRequiredWithSuggestions(
            "zona", f"{name} is split into several collection zones", suggestions
        )

    for zone_id, label in labels.items():
        if zona == zone_id or _normalise(zona) in (
            _normalise(label),
            _normalise(f"{name} {label}"),
        ):
            return zone_id
    if not suggestions:
        raise SourceArgumentNotFound(
            "zona",
            zona,
            f"{name} has a single collection zone, leave the zone empty",
        )
    raise SourceArgumentNotFoundWithSuggestions("zona", zona, suggestions)


def _events_url(zone_id: str, **_) -> str:
    return f"{API_URL}/objects/{zone_id}/relations/recycling_event_place"


def _page_count(
    response, zone_id: str, comune: str, zona: str | None = None, **_
) -> int:
    """How many pages of events the zone has, read from a one-item request."""
    body = response.json()
    if not body["data"]:
        argument, value = ("zona", zona) if zona else ("comune", comune)
        raise SourceArgumentNotFound(
            argument,
            value,
            "Mantova Ambiente publishes no collection calendar for it",
        )
    return math.ceil(body["paging"]["total"] / PAGE_SIZE)


def _waste(record: dict[str, Any]) -> str:
    """The waste type from an event title: "Gonzaga Zona 2 - Organico"."""
    return record["title"].rsplit(" - ", 1)[-1].strip()


def _date(record: dict[str, Any]) -> str:
    """The day of a date item ("2026-03-02T00:00:00+00:00"), without its time."""
    return record["date_item"]["start_date"][:10]


@final
class Source(BaseSource):
    TITLE = "Mantova Ambiente"
    DESCRIPTION = "Source for Mantova Ambiente (Gruppo TEA), Italy."
    URL = "https://www.mantovaambiente.it"
    COUNTRY = "it"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@matteolel"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Gonzaga Zona 1": {"comune": "Gonzaga", "zona": "Zona 1"},
        "Gonzaga Zona 2": {"comune": "Gonzaga", "zona": "Zona 2"},
        "Bagnolo San Vito": {"comune": "Bagnolo San Vito"},
        "Mantova quartieri Zona 1": {"comune": "Mantova", "zona": "quartieri Zona 1"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Gonzaga without zone": {"comune": "Gonzaga"},
    }

    PARAMS = (
        municipality(field="comune"),
        # A collection zone is a part of the municipality. YAML types a zone id
        # given as a bare number as an int, so it is coerced to text.
        text_field(
            "zona", term=field_terms.DISTRICT, optional=True, coerce=field_terms.as_text
        ),
    )

    REGIONS = regions.from_yaml("mantovaambiente_it", comune="title")

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality as it is named on "
            "https://www.mantovaambiente.it (e.g. Gonzaga). If the municipality "
            "is split into several collection zones, also enter your zone "
            "(e.g. Zona 1): on the municipality's page, the link "
            '"Non conosci la zona?" lists the streets and hamlets of each zone. '
            "Leave the zone empty for a municipality with a single zone; if it "
            "has several, the form then lists them."
        ),
        "it": (
            "Inserisci il comune come è indicato su https://www.mantovaambiente.it "
            "(es. Gonzaga). Se il comune è suddiviso in più zone di raccolta, "
            "inserisci anche la zona (es. Zona 1): nella pagina del comune, il "
            'link "Non conosci la zona?" elenca le vie e le frazioni di ogni zona. '
            "Lascia la zona vuota per un comune con una sola zona; se ne ha più "
            "di una, il modulo le elenca."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(f"{API_URL}/zones", pick=_zone_id, timeout=TIMEOUT),
            retrievers.Lookup(
                _events_url,
                params={"page_size": 1},
                pick=_page_count,
                timeout=TIMEOUT,
            ),
        ),
        targets=lambda source, context: range(1, context[1] + 1),
        fetch=retrievers.Request(
            lambda page, context, **_: _events_url(context[0]),
            params=lambda page, context, **_: {"page_size": PAGE_SIZE, "page": page},
            timeout=TIMEOUT,
        ),
    )
    parse = parsers.EachResponse(
        parsers.JsonParser("data", "objects", shape=list[_Event])
    )
    preprocess = Compose(
        ExplodeList("date_items", into="date_item"),
        Deduplicate(key=lambda record: (_date(record), _waste(record))),
    )
    transform = JsonTransformer(
        date_key=_date,
        type_key=_waste,
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Plastica": wt.RECYCLABLES,
            "Sfalci": wt.GARDEN_WASTE,
            # Quistello runs its grass-cutting round in four zones.
            "Sfalci zona 1": wt.GARDEN_WASTE,
            "Sfalci zona 2": wt.GARDEN_WASTE,
            "Sfalci zona 3": wt.GARDEN_WASTE,
            "Sfalci zona 4": wt.GARDEN_WASTE,
            # Nappies and incontinence pads are residual waste.
            "Pannolini e pannoloni": wt.GENERAL_WASTE,
            # Street sweeping: not a bin collection, but a dated event the
            # resident may want to see (as in siunet_it).
            "Spazzamento": wt.OTHER,
        },
    )
