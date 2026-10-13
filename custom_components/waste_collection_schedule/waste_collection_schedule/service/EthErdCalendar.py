"""EthErdCalendar retrieval and parsing, using the pipeline HTTP session."""

import datetime
import re
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

CITY_SLUG_MAP = {
    "érd": "erd",
    "diósd": "diosd",
    "sóskút": "soskut",
    "tárnok": "tarnok",
    "ráckeresztúr": "rackeresztur",
}
HTML_BASE_URL = "https://www.eth-erd.hu/storage/uploads/{slug}.html"


def _parse_date(date_str: str) -> datetime.date | None:
    """Parse date strings in format 'YYYY-M-D' (no zero-padding)."""
    try:
        parts = date_str.split("-")
        return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


class _CalendarClient:
    _session: Any

    def __init__(self, city: str, street: str = "") -> None:
        self._city = city
        self._street = street

    def retrieve(self) -> Any:
        session = self._session
        city_slug = CITY_SLUG_MAP.get(self._city.lower())
        if city_slug is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, list(CITY_SLUG_MAP.keys())
            )
        html_url = HTML_BASE_URL.format(slug=city_slug)
        r = session.get(html_url, timeout=30)
        r.raise_for_status()
        cdn_scripts = re.findall(
            'src="(https://cdn\\.jsdelivr\\.net/gh/[^"]+telepvegleges[^"]+\\.js)"',
            r.text,
        )
        if not cdn_scripts:
            raise SourceArgumentNotFound(
                "city",
                self._city,
                "Could not find the schedule data URL on the provider page.",
            )
        telepvegleges_url = cdn_scripts[0]
        r2 = session.get(telepvegleges_url, timeout=60)
        r2.raise_for_status()
        return r2

    def parse(self, response):
        js_content = response.text
        available_streets = re.findall("telep === '([^']+)'", js_content)
        if not available_streets:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "No street data found in the provider schedule file.",
            )
        if not self._street:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, available_streets
            )
        escaped = re.escape(self._street)
        block_match = re.search(
            f"telep === '{escaped}'(.+?)(?=telep === '|\\Z)", js_content, re.DOTALL
        )
        if block_match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, available_streets
            )
        block = block_match.group(1)
        assignments: dict[str, list[str]] = {}
        for date_str, css_class in re.findall(
            "'#a(\\d{4}-\\d+-\\d+)'\\)\\.addClass\\('([^']+)'\\)", block
        ):
            assignments.setdefault(date_str, []).append(css_class)
        entries: list[dict] = []
        for date_str, classes in assignments.items():
            d = _parse_date(date_str)
            if d is None:
                continue
            for css_class in classes:
                if css_class == "csakkomm":
                    entries.append({"date": d, "type": "Communal"})
                elif css_class == "kommszel":
                    entries.append({"date": d, "type": "Communal"})
                    entries.append({"date": d, "type": "Selective"})
                elif re.match("week\\d+$", css_class) or css_class == "kommzold":
                    entries.append({"date": d, "type": "Green"})
                    if css_class == "kommzold":
                        entries.append({"date": d, "type": "Communal"})
                elif css_class == "uvegszin":
                    entries.append({"date": d, "type": "Glass"})
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
