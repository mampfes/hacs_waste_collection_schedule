import base64
import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
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

ICON_MAP = {
    "restmüll": "mdi:trash-can",
    "gelber sack": "mdi:recycle",
    "gelbe tonne": "mdi:recycle",
    "blaue tonne": "mdi:recycle",
    "papier": "mdi:recycle",
    "bio": "mdi:leaf",
    "schadstoffmobil": "mdi:car-battery",
}


class Source:
    def __init__(self, city, street_number=None, street_name=None, house_number=""):
        self.city = str(city)
        self.city_code = CITY_CODE_MAP[city]

        if street_name is None and street_number is None:
            raise ValueError("Either street_name or street_number must be set")

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
            entries.append(Collection(d[0], name, ICON_MAP.get(name.lower())))

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
        raise ValueError(f"Street {self.street_name} not found")

    def get_dates(self, year: int, month: int) -> list:
        current_calendar = self.get_calendar_from_site(year)
        dates = self._ics.convert(current_calendar)

        # in december the calendar for the next year is available
        if month == 12:
            next_calendar = self.get_calendar_from_site(year + 1)
            dates += self._ics.convert(next_calendar)
        return dates

    def get_calendar_from_site(self, year: int) -> str:
        r = self._session.get(
            API_URL,
            params={
                "orteId": self.city_code,
                "strassenId": self.street_number,
                "fixedYear": str(year),
                "hausNr": f"'{self.house_number}'",
                "unixZeitOption": "0",
                "dateiName": f"'Abfallkalender{str(year)}.ics'",
            },
            headers={
                "Accept": "application/json, text/plain;q=0.5, text/calendar",
                "Accept-Encoding": "gzip, deflate, br",
            },
        )

        r.raise_for_status()

        return base64.b64decode(
            r.json()["d"]["ZeigeAbfallkalender"]["FileContents"]
        ).decode(
            "utf-8"
        )  # r.text
