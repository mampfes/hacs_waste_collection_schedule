import base64
import datetime
from typing import Literal

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Städteservice Raunheim Rüsselsheim"
DESCRIPTION = "Städteservice Raunheim Rüsselsheim"
URL = "https://www.staedteservice.de"
TEST_CASES = {
    "Rüsselsheim": {"city": "Rüsselsheim", "street_number": "411", "house_number": "3"},
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

API_URL = "https://portal.staedteservice.de/api/ZeigeAbfallkalender"

CITY_CODE_MAP = {"Rüsselsheim": 1, "Raunheim": 2}
CITIES = Literal["Rüsselsheim", "Raunheim"]

ICON_MAP = {
    "restmüll": "mdi:trash-can",
    "gelber sack": "mdi:recycle",
    "gelbe tonne": "mdi:recycle",
    "blaue tonne": "mdi:recycle",
    "papier": "mdi:recycle",
    "bio": "mdi:leaf",
    "glas": "mdi:glass-fragile",
    "schadstoffmobil": "mdi:car-battery",
}


class Source:
    def __init__(
        self, city: CITIES, street_number=None, street_name=None, house_number=""
    ):
        self.city = str(city)
        if city not in CITY_CODE_MAP:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", city, CITY_CODE_MAP.keys()
            )
        self.city_code = CITY_CODE_MAP[city]

        if street_name is None and street_number is None:
            raise SourceArgumentExceptionMultiple(
                ("street_name", "street_number"),
                "Either street_name or street_number must be set",
            )

        self.street_number = street_number
        self.street_name = street_name
        self.house_number = str(house_number)

        self._session = requests.Session()
        self._ics = ICS()

    def fetch(self) -> list:
        if not self.street_number:
            self.street_number = self.get_street(self.city_code)

        currentDateTime = datetime.datetime.now()
        year = currentDateTime.year
        month = currentDateTime.month

        dates = self.get_dates(year, month)

        entries = []
        for d in dates:
            name = d[1]
            name = name.replace("Abfuhr: ", "")
            entries.append(Collection(d[0], name, ICON_MAP.get(name.lower(), "mdi:trash-can")))

        return entries

    def get_street(self, city_id) -> int:
        r = self._session.get(
            "https://portal.staedteservice.de/api/Strassen",
            params={"$filter": f"Ort/OrteId eq {city_id}"},
            headers={"Accept": "application/json, text/plain;q=0.5, */*;q=0.1"},
        )
        r.raise_for_status()

        streets = r.json()["d"]
        for street in streets:
            if (
                street["Name"].replace(" ", "").lower()
                == self.street_name.replace(" ", "").lower()
            ):
                return street["StrassenId"]
        raise SourceArgumentNotFoundWithSuggestions(
            "street_name", self.street_name, [x["Name"] for x in streets]
        )

    def get_dates(self, year: int, month: int) -> list:
        current_calendar = self.get_calendar_from_site(year)
        dates = self._ics.convert(current_calendar)

        # in december the calendar for the next year is available
        if month == 12:
            next_calendar = self.get_calendar_from_site(year + 1)
            dates += self._ics.convert(next_calendar)
        return dates

    def get_calendar_from_site(self, year: int) -> str:
        payload = {
            "orteId": self.city_code,
            "strassenId": self.street_number,
            "hausNr": f"'{self.house_number}'",
            "dateiName": f"'Abfallkalender{year}.ics'",
            "unixZeitOption": "-25200",
            "fixedYear": str(year),
        }

        r = self._session.post(
            API_URL,
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
        ).decode(
            "utf-8"
        )
