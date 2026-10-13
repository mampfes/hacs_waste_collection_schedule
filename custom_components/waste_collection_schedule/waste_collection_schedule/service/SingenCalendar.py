"""SingenCalendar calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

import re
from datetime import date
from difflib import get_close_matches
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_OVERVIEW_URL = "https://www.stadtwerke-singen.de/abfall/abfallkalender/"
_GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def _extract_abfuhr_id(href: str) -> int | None:
    values = parse_qs(urlparse(href).query).get("abfuhr")
    return int(values[0]) if values else None


def _parse_range(part: str) -> tuple[int, int | None] | None:
    match = re.match("(\\d+)\\s*-\\s*(Ende|\\d+)", part.strip())
    if not match:
        return None
    low = int(match.group(1))
    high = None if match.group(2) == "Ende" else int(match.group(2))
    return (low, high)


def _house_number_in_range(house_number: int, suffix: str | None) -> bool:
    if suffix is None:
        return True
    body = suffix
    if body.lower().startswith("nr."):
        body = body[3:].strip()
    parts = re.split("\\s+u\\.\\s+", body)
    for part in parts:
        parsed = _parse_range(part)
        if parsed is None:
            continue
        low, high = parsed
        if house_number < low:
            continue
        if high is not None and house_number > high:
            continue
        if len(parts) > 1 and house_number % 2 != low % 2:
            continue
        return True
    return False


def _retrieve(source: BaseSource) -> Any:
    session = source.session
    base_url, year = _get_base_url(source, session)
    abfuhr_id = _resolve_abfuhr_id(source, session, base_url)
    r = session.get(base_url, params={"abfuhr": abfuhr_id}, timeout=30)
    r.raise_for_status()
    return (r, year)


def _get_base_url(source: BaseSource, session: Any) -> tuple[str, int]:
    r = session.get(_OVERVIEW_URL)
    r.raise_for_status()
    match = re.search(
        "https://www\\.stadtwerke-singen\\.de/abfall/abfallkalender-(\\d{4})/", r.text
    )
    if not match:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", source.params["street"], []
        )
    return (match.group(0), int(match.group(1)))


def _resolve_abfuhr_id(source: BaseSource, session: Any, base_url: str) -> int:
    r = session.get(base_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.select("div.districtdirectory a"):
        if a.get_text(strip=True).casefold() == source.params["street"].casefold():
            abfuhr_id = _extract_abfuhr_id(a["href"])
            if abfuhr_id is not None:
                return abfuhr_id
    letter = source.params["street"][0].casefold()
    r = session.get(base_url, params={"st": letter})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    entries: list[tuple[str, str, str | None, int]] = []
    street_list = soup.find("ul", class_="streetlist")
    if street_list:
        for a in street_list.find_all("a"):
            text = a.get_text(strip=True)
            abfuhr_id = _extract_abfuhr_id(a["href"])
            if abfuhr_id is None:
                continue
            match = re.match("^(.*?)\\s*\\((Nr\\..*)\\)\\s*$", text)
            if match:
                base_name, suffix = (match.group(1).strip(), match.group(2).strip())
            else:
                base_name, suffix = (text, None)
            entries.append((text, base_name, suffix, abfuhr_id))
    matches = [
        e for e in entries if e[1].casefold() == source.params["street"].casefold()
    ]
    if not matches:
        all_names = sorted({e[1] for e in entries})
        suggestions = get_close_matches(
            source.params["street"], all_names, n=5, cutoff=0.5
        )
        raise SourceArgumentNotFoundWithSuggestions(
            "street", source.params["street"], suggestions
        )
    if len(matches) == 1:
        return matches[0][3]
    if source.params["house_number"] is None:
        raise SourceArgumentRequiredWithSuggestions(
            "house_number",
            f"street '{source.params['street']}' is split into several address ranges",
            [m[0] for m in matches],
        )
    for _display, _base_name, suffix, abfuhr_id in matches:
        if _house_number_in_range(source.params["house_number"], suffix):
            return abfuhr_id
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", source.params["house_number"], [m[0] for m in matches]
    )


def _parse(source: BaseSource, raw) -> list[dict[str, Any]]:
    r, year = raw
    soup = BeautifulSoup(r.text, "html.parser")
    entries: list[dict] = []
    for div in soup.find_all("div", class_="muellresp"):
        h4 = div.find("h4")
        if not h4:
            continue
        waste_type = h4.get_text(strip=True)
        for wrapper in div.find_all("div", class_="collection-wrapper"):
            month_div = wrapper.find("div", class_="collection-month")
            date_div = wrapper.find("div", class_="collection-date")
            if not month_div or not date_div:
                continue
            month_name = month_div.get_text(strip=True).rstrip(":").casefold()
            month = _GERMAN_MONTHS.get(month_name)
            if month is None:
                continue
            for day_str in date_div.get_text(strip=True).split(","):
                day_str = day_str.strip().rstrip(".")
                if not day_str:
                    continue
                day = int(day_str.split(".")[0])
                entries.append({"date": date(year, month, day), "type": waste_type})
    for h4 in soup.find_all("h4"):
        title = h4.get_text(strip=True)
        if title != "Christbaumabfuhr":
            continue
        parent = h4.parent
        text = parent.get_text(" ", strip=True).replace(title, "", 1).strip()
        for match in re.findall("\\d{2}\\.\\d{2}\\.\\d{4}", text):
            day, month, year = (int(part) for part in match.split("."))
            entries.append({"date": date(year, month, day), "type": title})
    return entries


class CalendarRetriever(RetrieverFunc):
    """Retrieve the calendar and context needed to interpret it."""

    def __call__(self, source: BaseSource) -> Any:
        return _retrieve(source)


class CalendarParser(Parser[list[dict[str, Any]]]):
    """Read provider records without classifying their waste types."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        return _parse(source, response)
