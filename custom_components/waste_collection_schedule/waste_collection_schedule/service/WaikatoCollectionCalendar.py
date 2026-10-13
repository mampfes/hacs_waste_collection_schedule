"""WaikatoCollectionCalendar retrieval and parsing through the shared, verified HTTP session."""

import re
from datetime import datetime, timedelta
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_URL = "https://www.waikatodistrict.govt.nz/widgetApi/RubbishAndRecyclingCollections/search"
COLLECTION_TYPE = "Rubbish and Recycling"
WEEKS_AHEAD = 26
MAX_SUGGESTIONS = 10
WEEKDAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}
NO_WEEKLY_SERVICE_DAYS = {"", "selfservice", "monthlydropoff"}
_PUNCTUATION_RE = re.compile("[,\\n\\r]+")
_WHITESPACE_RE = re.compile("\\s+")


def _normalize(address: str) -> str:
    address = _PUNCTUATION_RE.sub(" ", address)
    address = _WHITESPACE_RE.sub(" ", address)
    return address.strip().lower()


class _CalendarClient:
    _session: Any

    def __init__(self, address: str):
        self._address: str = address.strip()

    def retrieve(self) -> Any:
        query = _normalize(self._address)
        r = self._session.get(API_URL, params={"address": query}, timeout=30)
        r.raise_for_status()
        return r

    def parse(self, r):
        query = _normalize(self._address)
        results = r.json()
        unique: dict[str, dict] = {}
        for entry in results:
            raw_address = entry.get("address")
            if not raw_address:
                continue
            key = _normalize(raw_address)
            unique.setdefault(key, entry)
        if not unique:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])
        exact = unique.get(query)
        if exact is not None:
            target = exact
        elif len(unique) == 1:
            target = next(iter(unique.values()))
        else:
            suggestions = sorted(e["address"] for e in unique.values())
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, suggestions[:MAX_SUGGESTIONS]
            )
        # New API records nest the published collection day/area/date.
        collections = target.get("collections")
        if collections is None:
            collections = [target]
        entries = []
        seen = set()
        for collection in collections:
            collection_day = (collection.get("collectionDay") or "").strip().lower()
            area = collection.get("collectionArea")
            next_date_str = collection.get("nextDate")
            if (
                collection_day in NO_WEEKLY_SERVICE_DAYS
                or collection_day not in WEEKDAYS
                or area in (None, "None")
                or not next_date_str
            ):
                continue
            next_date = datetime.fromisoformat(next_date_str).date()
            for i in range(WEEKS_AHEAD):
                collection_date = next_date + timedelta(weeks=i)
                if collection_date not in seen:
                    seen.add(collection_date)
                    entries.append({"date": collection_date, "type": COLLECTION_TYPE})
        if not entries:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "no fixed weekly collection service is published for this address",
            )
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
