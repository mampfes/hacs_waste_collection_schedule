"""Städteservice Raunheim Rüsselsheim (staedteservice.de).

Demonstrates: a JSON-wrapped-base64-ICS API. The calendar endpoint returns a
JSON envelope whose payload is the ICS feed itself, base64-encoded, and
(in December) must be requested twice -- the current and following year --
since the site starts publishing next year's calendar in December. No
configured retriever expresses "decode a base64 field out of a JSON
response, possibly twice", hence a source-defined ``retrieve()``/``parse()``
pair. The street can be supplied either as the portal's own opaque street id
(``street_number``, skipping the lookup) or as a human street name
(``street_name``, resolved against the portal's street list first).
"""

import base64
import datetime
from typing import ClassVar, final

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
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import RECYCLABLES

_API_URL = "https://portal.staedteservice.de/api/ZeigeAbfallkalender"
_STREETS_URL = "https://portal.staedteservice.de/api/Strassen"

_CITY_CODE_MAP = {"Rüsselsheim": 1, "Raunheim": 2}


@final
class Source(BaseSource):
    TITLE = "Städteservice Raunheim Rüsselsheim"
    DESCRIPTION = "Städteservice Raunheim Rüsselsheim"
    URL = "https://www.staedteservice.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

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

    def _get_street(self, session, city_code: int, street_name: str) -> str:
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

    def _get_calendar_text(
        self, session, city_code: int, street_number: str, house_number: str, year: int
    ) -> str:
        payload = {
            "orteId": city_code,
            "strassenId": street_number,
            "hausNr": f"'{house_number}'",
            "dateiName": f"'Abfallkalender{year}.ics'",
            "unixZeitOption": "-25200",
            "fixedYear": str(year),
        }
        r = session.post(
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
        return base64.b64decode(
            r.json()["d"]["ZeigeAbfallkalender"]["FileContents"]
        ).decode("utf-8")

    def retrieve(self, source):
        session = source.session
        city_code = _CITY_CODE_MAP[self.params["city"]]
        street_number = self.params.get("street_number")
        house_number = str(self.params.get("house_number") or "")

        if not street_number:
            street_number = self._get_street(
                session, city_code, self.params["street_name"]
            )

        now = datetime.datetime.now()
        texts = [
            self._get_calendar_text(
                session, city_code, street_number, house_number, now.year
            )
        ]
        # In December the calendar for the next year is already available.
        if now.month == 12:
            texts.append(
                self._get_calendar_text(
                    session, city_code, street_number, house_number, now.year + 1
                )
            )
        return texts

    def parse(self, texts, source):
        ics = ICS(regex=r"Abfuhr: (.*)")
        entries = []
        for text in texts:
            entries.extend(ics.convert(text))
        return entries
