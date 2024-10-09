from datetime import datetime
from typing import Literal, TypedDict

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
    "Borinka Weekly": {"city": "Borinka", "frequency": "weekly"},
    "Cerová Monthly": {"city": "Cerová", "frequency": "monthly"},
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
    defaultFrequencyTitle: str | None
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


FREQUENCIES_LITERAL = Literal["weekly", "biweekly", "monthly"]
FREQUENCIES: list[FREQUENCIES_LITERAL] = ["weekly", "biweekly", "monthly"]

DEFAULT_FREQUENCY_MAP: dict[str, FREQUENCIES_LITERAL] = {
    "dvojtýždenne": "biweekly",
    "týždenne": "weekly",
    "": "weekly",
}


class Source:
    def __init__(
        self,
        city: str,
        location: str | None = None,
        frequency: FREQUENCIES_LITERAL | None = None,
    ):
        self._city: str = city
        self._location: str | None = location
        self._frequency: FREQUENCIES_LITERAL | None = frequency

        if frequency and frequency not in FREQUENCIES:
            raise ValueError(
                f"Invalid frequency: {frequency}, must be one of {FREQUENCIES}"
            )

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
        data: OptionsResult = r.json()
        if len(data["frequencies"]) == 0:
            self._frequency = "weekly"
            return data
        if len(data["frequencies"]) == 1:
            self._frequency = FREQUENCIES[data["frequencies"][0] - 1]

        available_freqs: list[FREQUENCIES_LITERAL] = [
            FREQUENCIES[freq - 1] for freq in data["frequencies"]
        ]
        if self._frequency in available_freqs:
            return data

        changed: dict[str, FREQUENCIES_LITERAL] = dict()

        if (
            data["defaultFrequencyTitle"]
            and data["defaultFrequencyTitle"] in DEFAULT_FREQUENCY_MAP
            and "weekly" in available_freqs
        ):
            available_freqs.remove("weekly")
            available_freqs.append(DEFAULT_FREQUENCY_MAP[data["defaultFrequencyTitle"]])
            changed[DEFAULT_FREQUENCY_MAP[data["defaultFrequencyTitle"]]] = "weekly"

        if len(data["frequencies"]) > 1:
            if not self._frequency:
                raise SourceArgumentRequiredWithSuggestions(
                    "frequency", "for this location", available_freqs
                )

            if self._frequency not in available_freqs:
                raise SourceArgumentNotFoundWithSuggestions(
                    "frequency", self._frequency, available_freqs
                )
            if self._frequency in changed:
                self._frequency = changed[self._frequency]

        return data

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

    def _match_frequency(self, entry: CollecctionEntry) -> bool:
        if entry["wasteType"] != 1:
            return True
        if self._frequency == "weekly":
            return True
        if self._frequency == "biweekly":
            return entry["isBiweekly"]
        if self._frequency == "monthly":
            return entry["isMonthly"]
        return False

    def _get_collections_with_year(self, year: int) -> list[Collection]:
        if not self._location_id or not self._waste_dict:  # Should not happen
            raise Exception("Location ID and waste dict must be set")

        schedule = self.fetch_schedule(self._location_id, year)
        entries: list[Collection] = []
        for entry in schedule:
            if not self._match_frequency(entry):
                continue
            waste_type = self._waste_dict[entry["wasteId"]]
            date = parse(entry["date"]).date()
            icon = ICON_MAP.get(waste_type.split()[0])
            entries.append(Collection(date=date, t=waste_type, icon=icon))
        return entries
