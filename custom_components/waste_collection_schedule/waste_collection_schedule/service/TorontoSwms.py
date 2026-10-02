"""The City of Toronto Solid Waste Management Services collection calendar.

Toronto publishes one calendar for the whole city, ``collection_calendar.csv``,
with a row per collection area (``Friday2``, ``Tuesday1``, ...) and week. A
household's area is found through the city's address geocoder in two calls::

    geocoder/suggest               ?searchString=<address>  -> KEYSTRING of the address
    geocoder/findAddressCandidates ?keyString=<KEYSTRING>   -> AREACURSOR1: the area name

:class:`TorontoSwmsRetriever` resolves the area and downloads the calendar;
:class:`TorontoSwmsParser` keeps the rows of that area and yields one
``(date, stream)`` row per stream collected that week. A stream's cell holds
the letter of its weekday in the row's week (``M T W R F S X`` for Monday to
Sunday; ``0`` for none).
"""

import csv
import datetime
import io
from typing import TYPE_CHECKING, Any
from weakref import WeakKeyDictionary

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Lookup, Request, Response

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

CALENDAR_URL = "https://www.toronto.ca/ext/swms/collection_calendar.csv"
GEOCODER_URL = "https://map.toronto.ca/cotgeocoder/rest/geocoder"

_WEEKDAY_LETTERS = "MTWRFSX"

# The collection area each source resolved, handed from the retriever to the parser.
_AREAS: "WeakKeyDictionary[BaseSource, str]" = WeakKeyDictionary()


def _first_row(response: Any) -> "dict[str, Any] | None":
    rows = (response.json().get("result") or {}).get("rows") or []
    return rows[0] if rows else None


class TorontoSwmsRetriever:
    """Resolve the address to its collection area, then download the city calendar.

    Args:
        address: the name of the param holding the street address.
    """

    def __init__(self, address: str = "street_address"):
        self._address = address
        self._find_address = Lookup(
            f"{GEOCODER_URL}/suggest",
            params=lambda **params: {
                "f": "json",
                "matchAddress": 1,
                "matchPlaceName": 1,
                "matchPostalCode": 1,
                "addressOnly": 0,
                "retRowLimit": 100,
                "searchString": params[address],
            },
            pick=self._pick_key,
        )
        self._find_area = Lookup(
            f"{GEOCODER_URL}/findAddressCandidates",
            params=lambda key, **_: {
                "keyString": key,
                "unit": "%",
                "areaTypeCode1": "RESW",
            },
            pick=self._pick_area,
        )
        self._calendar = Request(CALENDAR_URL)

    def _pick_key(self, response: Any, *keys: Any, **params: Any) -> str:
        row = _first_row(response)
        if row is None or not row.get("KEYSTRING"):
            raise SourceArgumentNotFound(self._address, params[self._address])
        return str(row["KEYSTRING"])

    def _pick_area(self, response: Any, *keys: Any, **params: Any) -> str:
        row = _first_row(response)
        areas = ((row or {}).get("AREACURSOR1") or {}).get("array") or []
        if not areas or not areas[0].get("AREA_NAME"):
            raise SourceArgumentNotFound(
                self._address,
                params[self._address],
                message_addition="the address has no residential collection area.",
            )
        return str(areas[0]["AREA_NAME"])

    def __call__(self, source: "BaseSource") -> Response:
        key = self._find_address(source)
        area = self._find_area(source, (key,))
        _AREAS[source] = area
        return self._calendar(source)


class TorontoSwmsParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, stream)`` rows of the household's collection area."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        area = _AREAS.get(source) if source is not None else None
        reader = csv.DictReader(io.StringIO(response.text))
        # The header carries stray whitespace (" ChristmasTree").
        reader.fieldnames = [name.strip() for name in reader.fieldnames or []]
        rows = list(reader)
        response_shape.expect(
            bool(rows) and {"Calendar", "WeekStarting"} <= set(reader.fieldnames),
            source_name=response_shape.source_name(source),
            detail="collection calendar has no Calendar / WeekStarting columns",
            raw=response.text[:500],
        )
        streams = [
            name
            for name in reader.fieldnames
            if name not in ("_id", "Calendar", "WeekStarting")
        ]

        found: list[tuple[datetime.date, str]] = []
        for row in rows:
            if area is None or not (row["Calendar"] or "").startswith(area):
                continue
            week = datetime.date.fromisoformat(row["WeekStarting"])
            for stream in streams:
                letter = row.get(stream)
                if letter not in tuple(_WEEKDAY_LETTERS):
                    continue
                found.append(
                    (
                        week
                        + datetime.timedelta(
                            days=_WEEKDAY_LETTERS.index(letter) - week.weekday()
                        ),
                        stream,
                    )
                )
        return found
