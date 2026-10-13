"""HastingsCollectionCalendar retrieval and parsing through the shared, verified HTTP session."""

import datetime
import logging
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgAmbiguousWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)
API_URL = "https://data.napier.govt.nz/regional/hdc/widgets/collectiondays/do_collectiondays.php"
HEADERS = {"User-Agent": "Mozilla/5.0"}


class _CalendarClient:
    _session: Any

    def __init__(self, address):
        self._address = address

    def fetch_property_details(self):
        params = {"search": self._address, "council": "hdc", "type": "address"}
        try:
            response = self._session.get(
                "https://data.napier.govt.nz/regional/shared/widgets/propertysearch/do_search.php",
                params=params,
                headers=HEADERS,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                raise ValueError(f"Failed to locate address: {self._address}")
            if data[0].get("id") == "0" and "No record found for your search" in data[
                0
            ].get("value", ""):
                raise ValueError(f"No record found for address: {self._address}")
            if len(data) > 1:
                raise SourceArgAmbiguousWithSuggestions(
                    "address", self._address, [item.get("value", "") for item in data]
                )
            if (
                "valuation_id" not in data[0]
                or "sufi_id" not in data[0]
                or "ra_unique_id" not in data[0]
            ):
                raise ValueError(f"Expected keys not found in the response: {data[0]}")
            valuation_id = data[0]["valuation_id"]
            sufi_id = data[0]["sufi_id"]
            ra_unique_id = data[0]["ra_unique_id"]
            return (valuation_id, sufi_id, ra_unique_id)
        except (requests.RequestsError, ValueError) as e:
            raise ValueError(
                f"Failed while locating address: {self._address} with error: {e}"
            ) from e

    def retrieve(self):
        v, s, r = self.fetch_property_details()
        params = {"v": v, "s": s, "r": r}
        try:
            response = self._session.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestsError as e:
            raise ValueError(f"API request failed: {e}") from e
        if not data.get("success", False):
            raise ValueError("API response indicates failure.")
        html_content = data.get("html", "")
        if not html_content:
            _LOGGER.warning("No HTML content found in API response.")
            raise ValueError("No HTML content in API response.")
        return response

    def parse(self, response):
        html_content = response.json()["html"]
        soup = BeautifulSoup(html_content, "html.parser")
        entries = []
        tables = soup.find_all("table")
        for table in tables:
            th = table.find("th")
            if not th:
                _LOGGER.warning("No th element found in table.")
                continue
            collection_type = th.get_text(strip=True).replace(" collection", "")
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if not cells:
                    continue
                collection_info = cells[0].get_text(strip=True)
                if "Every" in collection_info:
                    days = collection_info.split(". ")[0].split("/")
                    for day in days:
                        target_weekday = datetime.datetime.strptime(day, "%A").weekday()
                        today = datetime.date.today()
                        today_weekday = today.weekday()
                        days_until_next_occurrence = (
                            target_weekday - today_weekday + 7
                        ) % 7
                        next_occurrence = today + datetime.timedelta(
                            days=days_until_next_occurrence
                        )
                        for i in range(-7, 8):
                            occurrence_date = next_occurrence + datetime.timedelta(
                                weeks=i
                            )
                            collection_date = occurrence_date
                            entries.append(
                                {
                                    "date": collection_date,
                                    "type": collection_type.capitalize(),
                                }
                            )
        if not entries:
            raise ValueError(
                f"No collection entries found for address: {self._address}"
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
