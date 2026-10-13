"""GoldenPlainsCalendar retrieval and parsing through the shared, verified HTTP session."""

import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

AUTOCOMPLETE_URL = "https://www.goldenplains.vic.gov.au/views-autocomplete-filters/addresses/page_3/ezi_address/0"
SCHEDULE_URL = "https://www.goldenplains.vic.gov.au/address-search"
CARD_TYPES = {
    "recycling": "Recycling",
    "rubbish": "Garbage",
    "fogo": "Glass",
}


class _CalendarClient:
    _session: Any

    def __init__(self, address: str):
        self._address = re.sub("\\s+", " ", address).strip()

    def retrieve(self) -> Any:
        session = self._session
        r = session.get(AUTOCOMPLETE_URL, params={"q": self._address}, timeout=30)
        r.raise_for_status()
        suggestions = r.json()
        if not suggestions:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])
        canonical = None
        for item in suggestions:
            if item["value"].upper() == self._address.upper():
                canonical = item["value"]
                break
        if canonical is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, [item["value"] for item in suggestions]
            )
        r = session.get(SCHEDULE_URL, params={"address": canonical}, timeout=30)
        r.raise_for_status()
        return r

    def parse(self, r):
        soup = BeautifulSoup(r.text, "html.parser")
        entries: list[dict] = []
        for css_class, waste_type in CARD_TYPES.items():
            card = soup.select_one(f"div.card.{css_class}")
            if not card:
                continue
            p = card.find("p")
            if not p:
                continue
            for date_str in p.stripped_strings:
                date_str = date_str.strip()
                if not date_str:
                    continue
                date_clean = re.sub("(\\d+)(st|nd|rd|th)", "\\1", date_str)
                try:
                    date = datetime.strptime(date_clean, "%d %B %Y").date()
                except ValueError:
                    continue
                entries.append({"date": date, "type": waste_type})
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
