"""SitevisionGarbageCalendar retrieval and parsing, using the pipeline HTTP session."""

import re
from datetime import date, timedelta
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

MUNICIPALITIES = {
    "bracke": "https://www.vattenmiljoresurs.se/bracke/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
    "berg": "https://www.vattenmiljoresurs.se/berg/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
    "harjedalen": "https://www.vattenmiljoresurs.se/harjedalen/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
}
_INTERVAL_WEEKS = {"h1": 1, "h2": 2, "h4": 4}
_WEEKDAY_MAP = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub("\\s+", " ", text)
    return text.strip()


def _address_matches(search: str, candidate: str) -> bool:
    """Return True if *search* matches a potentially multi-number *candidate* entry."""
    search = _normalize(search)
    candidate = _normalize(candidate)
    if search == candidate:
        return True
    candidate_street = re.sub("\\d.*", "", candidate).strip()
    search_street = re.sub("\\d.*", "", search).strip()
    if candidate_street != search_street:
        return False
    candidate_numbers: set[str] = set()
    for match in re.findall("\\d+(?:\\s*-\\s*\\d+)?", candidate):
        if "-" in match:
            start, end = re.split("\\s*-\\s*", match)
            for n in range(int(start), int(end) + 1):
                candidate_numbers.add(str(n))
        else:
            candidate_numbers.add(match.strip())
    search_numbers = re.findall("\\d+", search)
    return any(n in candidate_numbers for n in search_numbers)


def _collection_dates(freq_code: str) -> list[date]:
    """Convert a frequency code (e.g. 'h222') to a list of upcoming collection dates."""
    if len(freq_code) < 4 or not freq_code.startswith("h"):
        return []
    interval_key = freq_code[:2]
    odd_even = freq_code[2]
    weekday_code = freq_code[3]
    if weekday_code not in _WEEKDAY_MAP:
        return []
    target_weekday = _WEEKDAY_MAP[weekday_code]
    interval_weeks = _INTERVAL_WEEKS.get(interval_key)
    if interval_weeks is None:
        return []
    today = date.today()
    results: list[date] = []
    for offset in range(366):
        candidate = today + timedelta(days=offset)
        if candidate.weekday() != target_weekday:
            continue
        week_number = candidate.isocalendar().week
        if interval_key == "h1":
            results.append(candidate)
        elif interval_key == "h2":
            if (odd_even == "1" and week_number % 2 == 1) or (
                odd_even == "2" and week_number % 2 == 0
            ):
                results.append(candidate)
        elif interval_key == "h4":
            week_mod = week_number % 4
            target_mod = int(odd_even) % 4
            if week_mod == target_mod:
                results.append(candidate)
    return results


class _CalendarClient:
    _session: Any

    def __init__(self, municipality: str, street_address: str):
        municipality = municipality.lower().strip()
        if municipality not in MUNICIPALITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", municipality, list(MUNICIPALITIES.keys())
            )
        self._base_url = MUNICIPALITIES[municipality]
        self._street_address = street_address

    def retrieve(self) -> Any:
        session = self._session
        r = session.get(
            self._base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20
        )
        r.raise_for_status()
        gc_idx = r.text.find("sv-garbage-collection")
        if gc_idx == -1:
            raise ValueError(
                "Could not locate the garbage-collection portlet on the provider page. The website layout may have changed."
            )
        match = re.search('data-cid="([^"]+)"', r.text[gc_idx : gc_idx + 600])
        if not match:
            raise ValueError(
                "Could not extract the portlet target ID from the provider page. The website layout may have changed."
            )
        target = match.group(1)
        ajax_url = f"{self._base_url}?sv.target={target}&sv.{target}.route=/allAddresses&svAjaxReqParam=ajax"
        r2 = session.get(
            ajax_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
                "Referer": self._base_url,
            },
            timeout=20,
        )
        r2.raise_for_status()
        return r2

    def parse(self, r2):
        all_addresses = r2.json().get("allAddresses", [])
        matched = next(
            (
                entry
                for entry in all_addresses
                if _address_matches(self._street_address, entry.get("hamtstalle", ""))
            ),
            None,
        )
        if matched is None:
            raise SourceArgumentNotFound("street_address", self._street_address)
        freq_code = matched.get("tbfurenhkorlistarad_strtomningsfrekvenskod", "")
        collection_dates = _collection_dates(freq_code)
        return [{"date": d, "type": "Hushållsavfall"} for d in collection_dates]


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
