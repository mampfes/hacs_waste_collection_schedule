"""Städteservice Raunheim Rüsselsheim (staedteservice.de).

Demonstrates: a JSON-wrapped-base64-ICS API. The calendar endpoint returns a
JSON envelope whose payload is the ICS feed itself, base64-encoded, and
(in December) must be requested twice, the current and following year, since
the site starts publishing next year's calendar in December. That is
``retrievers.YearlyRetriever``: ``prepare`` resolves the street once (skipped
entirely when the user supplied the portal's own opaque ``street_number``
instead of a ``street_name``), and ``fetch`` posts one year's request.

Unpacking the envelope is ``IcsFeedsParser``'s ``unwrap``, so the feed reaches
``parsers.IcsParser`` as ordinary iCalendar text.
"""

import base64
import json
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import IcsFeedsParser
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://portal.staedteservice.de/api/ZeigeAbfallkalender"
_STREETS_URL = "https://portal.staedteservice.de/api/Strassen"

_CITY_CODE_MAP = {"Rüsselsheim": 1, "Raunheim": 2}


def _pick_street(response, *, street_name: str, **_) -> str:
    """The portal's opaque id for a street name in one of the two cities."""
    streets = response.json()["d"]
    for entry in streets:
        if (
            entry["Name"].replace(" ", "").lower()
            == street_name.replace(" ", "").lower()
        ):
            return entry["StrassenId"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_name", street_name, [x["Name"] for x in streets]
    )


def _calendar_request(year: int, street_id: str, *, city: str, **params) -> dict:
    """One year's calendar request; the response body is the JSON envelope."""
    house_number_value = str(params.get("house_number") or "")
    return {
        "orteId": _CITY_CODE_MAP[city],
        "strassenId": street_id,
        "hausNr": f"'{house_number_value}'",
        "dateiName": f"'Abfallkalender{year}.ics'",
        "unixZeitOption": "-25200",
        "fixedYear": str(year),
    }


def _ics_from_envelope(body: str) -> str:
    """The iCalendar document the JSON envelope carries, base64-encoded."""
    encoded = json.loads(body)["d"]["ZeigeAbfallkalender"]["FileContents"]
    return base64.b64decode(encoded).decode("utf-8")


@final
class Source(BaseSource):
    TITLE = "Städteservice Raunheim Rüsselsheim"
    DESCRIPTION = "Städteservice Raunheim Rüsselsheim"
    URL = "https://www.staedteservice.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rüsselsheim": {
            "city": "Rüsselsheim",
            "street_number": "411",
            "house_number": "3",
        },
        "Raunheim": {
            "city": "Raunheim",
            "street_name": "wilhelm-Busch-Straße",
            "house_number": 3,
        },
        "Raunheim Rober-Koch-Straße 10 /1": {
            "city": "Raunheim",
            "street_name": "Robert-Koch-Straße",
            "house_number": "10 /1",
        },
    }

    PARAMS = (
        dropdown("city", options=list(_CITY_CODE_MAP), label="City"),
        text_field("street_number", "Street ID", optional=True),
        street(field="street_name", optional=True),
        house_number(field="house_number", optional=True),
    )

    retrieve = retrievers.YearlyRetriever(
        # The street id: the one given, or the one the street name resolves to.
        prepare=retrievers.Lookup(
            _STREETS_URL,
            params=lambda city, **_: {
                "$filter": f"Ort/OrteId eq {_CITY_CODE_MAP[city]}"
            },
            headers={"Accept": "application/json, text/plain;q=0.5, */*;q=0.1"},
            given=lambda street_number=None, **_: street_number or None,
            pick=_pick_street,
        ),
        fetch=retrievers.Request(
            _API_URL,
            method="POST",
            params=_calendar_request,
            data=_calendar_request,
            headers={
                "Accept": "application/json, text/plain;q=0.5, text/calendar",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (HomeAssistant)",
            },
        ),
    )

    parse = IcsFeedsParser(
        parsers.IcsParser(regex=r"Abfuhr: (.*)"),
        unwrap=_ics_from_envelope,
    )

    transform = ICSTransformer(type_value_map={"blaue tonne": wt.RECYCLABLES})

    def __init__(
        self,
        city: str,
        street_number=None,
        street_name=None,
        house_number="",
    ):
        super().__init__(
            city=city,
            street_number=street_number,
            street_name=street_name,
            house_number=house_number,
        )
        if city not in _CITY_CODE_MAP:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", city, _CITY_CODE_MAP.keys()
            )
        if street_name is None and street_number is None:
            raise SourceArgumentExceptionMultiple(
                ("street_name", "street_number"),
                "Either street_name or street_number must be set",
            )
