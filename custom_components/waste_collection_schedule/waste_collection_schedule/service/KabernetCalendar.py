"""KabernetCalendar retrieval and parsing, using the pipeline HTTP session."""

from datetime import datetime
from typing import Any, Literal, TypedDict

from dateutil.parser import parse

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc


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


def cmp(a: str, b: str) -> bool:
    return a.lower().replace(" ", "") == b.lower().replace(" ", "")


FREQUENCIES_LITERAL = Literal["weekly", "biweekly", "monthly"]
FREQUENCIES: list[FREQUENCIES_LITERAL] = ["weekly", "biweekly", "monthly"]
DEFAULT_FREQUENCY_MAP: dict[str, FREQUENCIES_LITERAL] = {
    "dvojtýždenne": "biweekly",
    "týždenne": "weekly",
    "": "weekly",
}


class _CalendarClient:
    _session: Any

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
        r = self._session.get(
            API_URL + "/location", params={"includeLocations": "True"}
        )
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
                [location for city in matches for location in city["locations"] or []],
            )
        for city in matches:
            if any(
                cmp(location, self._location) for location in city["locations"] or []
            ):
                return city
        raise SourceArgumentNotFoundWithSuggestions(
            "location",
            self._location,
            [location for city in matches for location in city["locations"] or []],
        )

    def fetch_options(self, location_id: int) -> OptionsResult:
        r = self._session.get(
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
        changed: dict[str, FREQUENCIES_LITERAL] = {}
        if (
            data["defaultFrequencyTitle"]
            and data["defaultFrequencyTitle"] in DEFAULT_FREQUENCY_MAP
            and ("weekly" in available_freqs)
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
        r = self._session.get(
            API_URL + "/schedule", params={"locationId": location_id, "year": year}
        )
        r.raise_for_status()
        return r

    def retrieve(self):
        self._location_id = self.fetch_city()["locationId"]
        self._waste_dict = self.get_waste_dict(self._location_id)
        now = datetime.now()
        years = [now.year]
        if now.month == 12:
            years.append(now.year + 1)
        responses = []
        for year in years:
            response = self.fetch_schedule(self._location_id, year)
            responses.append(response)
        return responses, self._waste_dict, self._frequency

    def parse(self, raw):
        responses, self._waste_dict, self._frequency = raw
        if self._waste_dict is None:
            raise ValueError("The calendar response contains no waste-type lookup")
        entries = []
        for response in responses:
            for entry in response.json():
                if self._match_frequency(entry):
                    entries.append(
                        {
                            "date": parse(entry["date"]).date(),
                            "type": self._waste_dict[entry["wasteId"]],
                        }
                    )
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


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
