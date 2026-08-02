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
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://portal.staedteservice.de/api/ZeigeAbfallkalender"
_STREETS_URL = "https://portal.staedteservice.de/api/Strassen"

_CITY_CODE_MAP = {"Rüsselsheim": 1, "Raunheim": 2}


def _lookup_street(session, city_code: int, street_name: str) -> str:
    """The portal's opaque id for a street name in one of the two cities."""
    r = session.get(
        _STREETS_URL,
        params={"$filter": f"Ort/OrteId eq {city_code}"},
        headers={"Accept": "application/json, text/plain;q=0.5, */*;q=0.1"},
    )
    r.raise_for_status()

    streets = r.json()["d"]
    for entry in streets:
        if (
            entry["Name"].replace(" ", "").lower()
            == street_name.replace(" ", "").lower()
        ):
            return entry["StrassenId"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_name", street_name, [x["Name"] for x in streets]
    )


def _resolve_address(source) -> tuple[int, str, str]:
    """City code, street id and house number, resolving the street if needed."""
    city_code = _CITY_CODE_MAP[source.params["city"]]
    street_number = source.params.get("street_number")
    house_number_value = str(source.params.get("house_number") or "")
    if not street_number:
        street_number = _lookup_street(
            source.session, city_code, source.params["street_name"]
        )
    return city_code, street_number, house_number_value


def _calendar_for_year(source, year: int, context: tuple[int, str, str]):
    """One year's calendar request; the response body is the JSON envelope."""
    city_code, street_number, house_number_value = context
    payload = {
        "orteId": city_code,
        "strassenId": street_number,
        "hausNr": f"'{house_number_value}'",
        "dateiName": f"'Abfallkalender{year}.ics'",
        "unixZeitOption": "-25200",
        "fixedYear": str(year),
    }
    r = source.session.post(
        _API_URL,
        params=payload,
        data=payload,
        headers={
            "Accept": "application/json, text/plain;q=0.5, text/calendar",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (HomeAssistant)",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r


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
        GENERAL_WASTE,
        GLASS,
        HAZARDOUS,
        ORGANIC,
        PAPER,
        RECYCLABLES,
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
        prepare=_resolve_address,
        fetch=_calendar_for_year,
    )

    parse = IcsFeedsParser(
        parsers.IcsParser(regex=r"Abfuhr: (.*)"),
        unwrap=_ics_from_envelope,
    )

    transform = ICSTransformer(type_value_map={"blaue tonne": RECYCLABLES})

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
