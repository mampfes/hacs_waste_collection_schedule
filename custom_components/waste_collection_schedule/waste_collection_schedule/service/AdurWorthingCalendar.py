"""AdurWorthingCalendar retrieval and parsing, using the pipeline HTTP session."""

import re
from datetime import datetime, timedelta
from typing import Any

import bs4
from dateutil import parser

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

NEXT_RE = re.compile("Next\\s+collection(?:\\s+dates?)?\\s*:", re.IGNORECASE)
DATE_RE = re.compile(
    "\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+(January|February|March|April|May|June|July|August|September|October|November|December)\\b",
    re.IGNORECASE,
)
HEADERS = {"user-agent": "Mozilla/5.0"}


class _CalendarClient:
    _session: Any

    def __init__(self, postcode=None, address=None, uprn=None):
        if uprn is not None:
            self._uprn = uprn
            self._postcode = None
            self._address = None
        else:
            self._postcode = postcode
            self._address = address
            self._uprn = None

    def retrieve(self):
        s = self._session
        if self._uprn is not None:
            r = s.get(
                f"https://www.adur-worthing.gov.uk/bin-day/?brlu-selected-address={self._uprn}",
                headers=HEADERS,
            )
            r.raise_for_status()
            html_collections = r.content
        else:
            if self._postcode is None or self._address is None:
                raise SourceArgumentExceptionMultiple(
                    ["postcode", "address"],
                    "either postcode or address needs to be provided but neither was",
                )
            postcode_search_request = s.get(
                f"https://www.adur-worthing.gov.uk/bin-day/?brlu-address-postcode={self._postcode}&return-url=/bin-day/&action=search",
                headers=HEADERS,
            )
            postcode_search_request.raise_for_status()
            html_addresses = postcode_search_request.content
            addresses = bs4.BeautifulSoup(html_addresses, "html.parser")
            addresses_select = addresses.find("select", {"id": "brlu-selected-address"})
            if addresses_select is None:
                raise ValueError("Could not find address selection form")
            found_address = None
            for address in addresses_select.find_all("option"):
                if self._address.upper() in address.get_text().upper():
                    found_address = address
            if found_address is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "address",
                    self._address,
                    [a.get_text() for a in addresses_select.find_all("option")],
                )
            collections_request = s.get(
                f"https://www.adur-worthing.gov.uk/bin-day/?brlu-selected-address={found_address['value']}&return-url=/bin-day/",
                headers=HEADERS,
            )
            collections_request.raise_for_status()
            html_collections = collections_request.content
        return html_collections

    def parse(self, html_collections):
        bin_collections = bs4.BeautifulSoup(html_collections, "html.parser")
        containers = bin_collections.find_all(
            "div", {"class": "bin-collection-listing-row row"}
        )
        entries = []
        today = datetime.now().date()
        for container in containers:
            waste_heading = container.find("h2")
            if waste_heading is None:
                continue
            waste_type = waste_heading.text
            waste_type = " ".join(waste_type.split())
            if waste_type == "General rubbish":
                waste_type = "Refuse"
            if waste_type.startswith("Garden waste"):
                waste_type = "Garden"
            dates = set()
            for text in container.find_all("p"):
                content = text.get_text(" ")
                if not NEXT_RE.search(content):
                    continue
                for day, month in DATE_RE.findall(content):
                    try:
                        d = parser.parse(f"{day} {month} {today.year}").date()
                    except (ValueError, OverflowError):
                        continue
                    if d < today - timedelta(days=60):
                        d = d.replace(year=d.year + 1)
                    if d >= today:
                        dates.add(d)
            for d in sorted(dates):
                entries.append({"type": waste_type, "date": d})
        if not entries:
            raise ValueError("No upcoming collection dates found")
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
