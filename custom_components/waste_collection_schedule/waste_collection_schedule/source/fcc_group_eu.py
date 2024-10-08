from datetime import datetime
from typing import TypedDict

import requests
from dateutil.parser import parse
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "fcc Environment"
DESCRIPTION = "Source for fcc Environment."
URL = "https://www.fcc-group.eu/"
TEST_CASES = {
    "Cífer J. Kubányiho": {
        "city": "Cífer",
        "location": "J. Kubányiho",
    },
    "Borinka": {
        "city": "Borinka",
    },
}

COUNTRY = "sk"


ICON_MAP = {
    "Komunálny": "mdi:trash-can",
    "Plasty": "mdi:recycle",
    "Papier": "mdi:package-variant",
    "Separovaný": "mdi:recycle",
}


class City(TypedDict):
    locationId: int
    city: str
    code: str
    defaultFrequencyTitle: None | str
    locations: None | list[str]


class Waste(TypedDict):
    wasteId: int
    title: str
    type: int


class OptionsResult(TypedDict):
    defaultFrequencyTitl: str | None
    frequencies: list[int]
    wastes: list[Waste]


class CollecctionEntry(TypedDict):
    scheduleId: int
    wasteId: int
    wasteType: int
    date: str
    isBiweekly: bool
    isMonthly: bool


API_URL = "https://vylozsmeti.kabernet.sk/api/public"


def cmp(a: str, b: str) -> bool:  # type: ignore[attr-defined]
    return a.lower().replace(" ", "") == b.lower().replace(" ", "")


class Source:
    def __init__(self, city: str, location: str | None = None):
        self._city: str = city
        self._location: str | None = location

        self._location_id: int | None = None
        self._waste_dict: dict[int, str] | None = None

    def fetch_city(self) -> City:
        r = requests.get(API_URL + "/location", params={"includeLocations": "True"})
        r.raise_for_status()
        data: list[City] = r.json()
        matches = []
        for city in data:
            if cmp(city["city"], self._city) or cmp(city["code"], self._city):
                matches.append(city)
        if len(matches) == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, [city["city"] for city in data]
            )
        if len(matches) == 1:
            return matches[0]

        if not self._location:
            raise SourceArgumentRequiredWithSuggestions(
                "location",
                "for this city",
                [
                    location
                    for city in matches
                    for location in (city["locations"] or [])
                ],
            )

        for city in matches:
            if any(
                cmp(location, self._location) for location in (city["locations"] or [])
            ):
                return city

        raise SourceArgumentNotFoundWithSuggestions(
            "location",
            self._location,
            [location for city in matches for location in (city["locations"] or [])],
        )

    def fetch_options(self, location_id: int) -> OptionsResult:
        r = requests.get(
            API_URL + "/schedule/options", params={"locationId": location_id}
        )
        r.raise_for_status()
        return r.json()

    def get_waste_dict(self, location_id: int) -> dict[int, str]:
        options = self.fetch_options(location_id)
        return {waste["wasteId"]: waste["title"] for waste in options["wastes"]}

    def fetch_schedule(self, location_id: int, year: int) -> list[CollecctionEntry]:
        r = requests.get(
            API_URL + "/schedule", params={"locationId": location_id, "year": year}
        )
        r.raise_for_status()
        return r.json()

    def fetch(self) -> list[Collection]:
        fresh_data = False
        if not self._location_id:
            fresh_data = True
            city = self.fetch_city()
            self._location_id = city["locationId"]
        if not self._waste_dict:
            self._waste_dict = self.get_waste_dict(self._location_id)

        try:
            return self._get_collections()
        except Exception:
            if fresh_data:
                raise
            self._location_id = self.fetch_city()["locationId"]
            self._waste_dict = self.get_waste_dict(self._location_id)
            return self._get_collections()

    def _get_collections(self) -> list[Collection]:
        now = datetime.now()
        year = now.year
        entries = self._get_collections_with_year(year)
        if now.month == 12:
            try:
                entries += self._get_collections_with_year(year + 1)
            except Exception:
                pass
        return entries

    def _get_collections_with_year(self, year: int) -> list[Collection]:
        if not self._location_id or not self._waste_dict:  # Should not happen
            raise Exception("Location ID and waste dict must be set")

        schedule = self.fetch_schedule(self._location_id, year)

        entries: list[Collection] = []
        for entry in schedule:
            waste_type = self._waste_dict[entry["wasteId"]]
            date = parse(entry["date"]).date()
            icon = ICON_MAP.get(waste_type.split()[0])
            entries.append(Collection(date=date, t=waste_type, icon=icon))
        return entries
