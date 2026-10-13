"""TheHillsCalendar retrieval and parsing through the shared, verified HTTP session."""

import datetime
import json
import logging
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)


class _CalendarClient:
    _session: Any

    def __init__(self, suburb, street, houseNo):
        self._suburb = suburb
        self._street = street
        self._houseNo = str(houseNo)
        self._url = "https://apps.thehills.nsw.gov.au/seamlessproxy/api"

    def retrieve(self):
        r = self._session.get(f"{self._url}/suburbs/get")
        data = json.loads(r.text)
        suburbs = {}
        for entry in data:
            suburbs[entry["Suburb"].strip().upper().replace(" ", "")] = entry[
                "SuburbKey"
            ]
        suburb_search = self._suburb.strip().upper().replace(" ", "")
        if suburb_search not in suburbs:
            raise SourceArgumentNotFoundWithSuggestions(
                "suburb", self._suburb, suburbs.keys()
            )
        suburb_key = suburbs[suburb_search]
        r = self._session.get(f"{self._url}/streets/{suburb_key}")
        data = json.loads(r.text)
        streets = {}
        for entry in data:
            streets[entry["Street"].strip().upper().replace(" ", "")] = entry[
                "StreetKey"
            ]
        street_search = self._street.strip().upper().replace(" ", "")
        if street_search not in streets:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, streets.keys()
            )
        street_key = streets[street_search]
        params = {"streetkey": street_key, "suburbKey": suburb_key}
        r = self._session.get(
            f"{self._url}/properties/GetPropertiesByStreetAndSuburbKey", params=params
        )
        data = json.loads(r.text)
        house_numbers = {}
        for entry in data:
            house_numbers[
                (str(int(entry["HouseNo"])) + entry.get("HouseSuffix", "").strip())
                .strip()
                .upper()
                .replace(" ", "")
            ] = entry["PropertyKey"]
        houseNo_search = self._houseNo.strip().upper().replace(" ", "")
        if houseNo_search not in house_numbers:
            raise SourceArgumentNotFoundWithSuggestions(
                "houseNo", self._houseNo, house_numbers.keys()
            )
        property_key = house_numbers[houseNo_search]
        r = self._session.get(f"{self._url}/services/{property_key}")
        return r

    def parse(self, r):
        data = json.loads(r.text)
        entries = []
        for entry in data:
            name = entry["Name"]
            for dateStr in entry["CollectionDays"]:
                date = datetime.datetime.strptime(dateStr, "%Y-%m-%dT%H:%M:%S").date()
                entries.append({"date": date, "type": name})
        return entries


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
