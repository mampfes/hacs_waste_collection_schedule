"""BarrieCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

FORM_URL = "https://sites.barrie.ca/barrieforms/Collection.aspx"
EVENTS_URL = "https://sites.barrie.ca/barrieforms/Scripts/collection_events.json"
DAY_ABBREVIATIONS = {
    "Mon": "Monday",
    "Tue": "Tuesday",
    "Wed": "Wednesday",
    "Thu": "Thursday",
    "Fri": "Friday",
    "Sat": "Saturday",
    "Sun": "Sunday",
}
WASTE_COMPONENTS = [
    ("Yard Waste", "Yard Waste"),
    ("Textile Collection", "Textile Collection"),
    ("Battery", "Battery Collection"),
    ("Tree", "Christmas Tree"),
    ("Garbage", "Garbage"),
    ("Recycling", "Recycling"),
    ("Organics", "Organics"),
]
SKIP_SUMMARIES = {"Cart Notice"}


def _expand_day_abbreviation(area_code: str) -> str:
    """Expand day abbreviations in area codes (e.g. 'Wed Area B' -> 'Wednesday Area B')."""
    return re.sub(
        "\\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\b",
        lambda m: DAY_ABBREVIATIONS.get(m.group(), m.group()),
        area_code,
    )


def _split_summary(summary: str) -> list[str]:
    """Split a compound summary into (label, icon) pairs."""
    results = []
    for keyword, label in WASTE_COMPONENTS:
        if keyword in summary:
            results.append(label)
    return results


class _CalendarClient:
    _session: Any

    def __init__(self, street_number: str, street_name: str):
        self._street_number = str(street_number).strip()
        self._street_name = street_name.strip().upper()

    def retrieve(self) -> Any:
        session = self._session
        r = session.get(FORM_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})
        form_data = {
            "__VIEWSTATE": viewstate["value"] if viewstate else "",
            "__VIEWSTATEGENERATOR": viewstate_gen["value"] if viewstate_gen else "",
            "__EVENTVALIDATION": event_validation["value"] if event_validation else "",
            "ctl00$MainContent$txtStreetNo": self._street_number,
            "ctl00$MainContent$txtStreet": self._street_name,
            "ctl00$MainContent$btnSubmit": "Submit",
        }
        r = session.post(FORM_URL, data=form_data, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        calendar_el = soup.find(id="MainContent_calendar_ID")
        if not calendar_el:
            raise SourceArgumentNotFound(
                "street_name",
                self._street_name,
                "no collection area found for this address.",
            )
        area_code = calendar_el.get_text(strip=True)
        if not area_code:
            raise SourceArgumentNotFound(
                "street_name",
                self._street_name,
                "no collection area found for this address.",
            )
        area_key = _expand_day_abbreviation(area_code)
        r = session.get(EVENTS_URL, timeout=30)
        r.raise_for_status()
        return r, area_key

    def parse(self, raw):
        r, area_key = raw
        all_events = r.json()
        if area_key not in all_events:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name",
                f"{self._street_name} (area: {area_key})",
                list(all_events.keys()),
            )
        events = all_events[area_key]
        no_location = all_events.get("No Location", [])
        entries: list[dict] = []
        now = datetime.now().date()
        for event in events + no_location:
            summary = event.get("summary", "")
            if summary in SKIP_SUMMARIES:
                continue
            date = datetime.strptime(event["start"], "%Y-%m-%d").date()
            if date < now:
                continue
            components = _split_summary(summary)
            if not components:
                entries.append({"date": date, "type": summary})
            else:
                for label in components:
                    entries.append({"date": date, "type": label})
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
