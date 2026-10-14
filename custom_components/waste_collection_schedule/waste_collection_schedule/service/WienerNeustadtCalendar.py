"""WienerNeustadtCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import re
from datetime import datetime
from typing import Any, Literal

from bs4 import BeautifulSoup
from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

RM_ART_MAP = {
    "wöchentlich": "31",
    "weekly": "31",
    "31": "31",
    "14-tägig": "33",
    "2weeks": "33",
    "bi-weekly": "33",
    "33": "33",
    "monatlich": "36",
    "monthly": "36",
    "36": "36",
}


class _CalendarClient:
    _session: Any

    def __init__(
        self,
        street: str,
        str_id: str | None = None,
        rm_art: Literal["wöchentlich", "14-tägig", "monatlich"] = "monatlich",
    ):
        """Initialize the Wiener Neustadt waste collection source.

        Args:
            street: Street name in Wiener Neustadt
            str_id: Optional street ID (if known, skips street lookup)
            rm_art: Collection frequency: 'wöchentlich', '14-tägig', or 'monatlich'

        Note:
            All waste types are always fetched.
            Use the integration's customize feature to filter or hide specific waste types.
        """
        self._street = street
        self._str_id = str_id
        self._rm_art = RM_ART_MAP.get(rm_art.lower(), "36")
        self._base_url = "https://abfall.wiener-neustadt.at"

    def retrieve(self) -> Any:
        """Fetch waste collection schedule for Wiener Neustadt.

        Returns:
            List of Collection objects

        Raises:
            Exception: If street not found or data cannot be retrieved
        """
        if not self._str_id:
            self._str_id, str_name_full, tn_ez_zone = self._lookup_street()
        else:
            str_name_full = None
            tn_ez_zone = None
        entries = self._fetch_schedule(self._str_id, str_name_full, tn_ez_zone)
        return entries

    def _lookup_street(self) -> tuple[str, str | None, str | None]:
        """Look up street ID from street name using the ASP backend.

        Returns:
            Tuple of (street_id, full_street_name, tn_ez_zone)

        Raises:
            SourceArgumentNotFoundWithSuggestions: If street not found
        """
        current_year = datetime.now().year
        first_letter = self._street[0].upper() if self._street else "A"
        initial_url = (
            f"{self._base_url}/vb_wn_termine.asp?bst={first_letter}&jahr={current_year}"
        )
        try:
            response = self._session.get(initial_url, timeout=30)
            response.raise_for_status()
        except requests.RequestsError as e:
            raise ValueError(
                f"Failed to connect to {self._base_url}. Please check your internet connection and verify the website is accessible. Error: {e}"
            ) from e
        soup = BeautifulSoup(response.content, "html.parser")
        str_id = None
        str_name_full = None
        tn_ez_zone = None
        street_normalized = (
            self._street.lower()
            .replace("ß", "ss")
            .replace("ä", "a")
            .replace("ö", "o")
            .replace("ü", "u")
        )
        found_streets = []
        for select in soup.find_all("select", {"name": "str_id"}):
            for option in select.find_all("option"):
                option_text = option.get_text().strip()
                value = option.get("value") or ""
                if not isinstance(value, str):
                    raise ValueError("Invalid street identifier")
                option_value = value.strip()
                if not option_value or option_value == "0":
                    continue
                option_normalized = (
                    option_text.lower()
                    .replace("ß", "ss")
                    .replace("ä", "a")
                    .replace("ö", "o")
                    .replace("ü", "u")
                )
                found_streets.append((option_text, option_value))
                if street_normalized == option_normalized:
                    str_id = option_value
                    str_name_full = option_text
                    break
            if str_id:
                break
        if not str_id:
            suggestions = [s[0] for s in found_streets[:20]]
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, suggestions
            )
        tn_ez_zone_input = soup.find("input", {"name": "tn_ez_zone", "type": "hidden"})
        if tn_ez_zone_input:
            value = tn_ez_zone_input.get("value")
            if value is not None and not isinstance(value, str):
                raise ValueError("Invalid collection zone")
            tn_ez_zone = value
        try:
            reload_response = self._session.post(
                initial_url, data={"str_id": str_id}, timeout=30
            )
            reload_response.raise_for_status()
        except requests.RequestsError as e:
            raise ValueError(
                f"Failed to retrieve zone information for street '{str_name_full}'. The website may be temporarily unavailable. Error: {e}"
            ) from e
        reload_soup = BeautifulSoup(reload_response.content, "html.parser")
        tn_ez_zone_input = reload_soup.find(
            "input", {"name": "tn_ez_zone", "type": "hidden"}
        )
        if tn_ez_zone_input:
            value = tn_ez_zone_input.get("value")
            if value is not None and not isinstance(value, str):
                raise ValueError("Invalid collection zone")
            tn_ez_zone = value
        str_name_input = reload_soup.find(
            "input", {"name": "str_name", "type": "hidden"}
        )
        if str_name_input:
            value = str_name_input.get("value")
            if value is not None and not isinstance(value, str):
                raise ValueError("Invalid collection street name")
            str_name_full = value
        return (str_id, str_name_full, tn_ez_zone)

    def _fetch_schedule(
        self, str_id: str, str_name_full: str | None, tn_ez_zone: str | None
    ) -> list[dict]:
        """Fetch and parse the waste collection schedule.

        Args:
            str_id: Street ID
            str_name_full: Full street name (optional)
            tn_ez_zone: Zone information (optional)

        Returns:
            List of Collection objects
        """
        current_year = datetime.now().year
        if datetime.now().month == 12:
            year = current_year + 1
        else:
            year = current_year
        if str_name_full:
            first_letter = str_name_full[0].upper()
        else:
            first_letter = self._street[0].upper()
        post_url = f"{self._base_url}/vb_wn_termine.asp?bst={first_letter}&jahr={year}"
        post_data = {
            "str_id": str_id,
            "rm_art": self._rm_art,
            "chk_biotonne": "ja",
            "chk_wertstoffe": "ja",
            "chk_altkleider": "ja",
            "chk_christbaum": "ja",
        }
        if tn_ez_zone:
            post_data["tn_ez_zone"] = tn_ez_zone
        if str_name_full:
            post_data["str_name"] = str_name_full
        try:
            response = self._session.post(post_url, data=post_data, timeout=30)
            response.raise_for_status()
        except requests.RequestsError as e:
            raise ValueError(
                f"Failed to fetch collection schedule for street ID '{str_id}'. The website may be temporarily unavailable or the street ID is invalid. Error: {e}"
            ) from e
        return response

    def parse(self, response):
        return self._parse_schedule(response.content)

    def _parse_schedule(self, html: str | bytes) -> list[dict]:
        """Parse collection schedule from HTML response.

        Args:
            html: HTML response text

        Returns:
            List of Collection objects

        Raises:
            Exception: If no collection dates found
        """
        entries = []
        soup = BeautifulSoup(html, "html.parser")
        date_pattern = re.compile("(\\d{2})\\.(\\d{2})\\.(\\d{4})\\s+(.*)")
        for div in soup.find_all("div"):
            text = div.get_text(" ", strip=True)
            match = date_pattern.match(text)
            if not match:
                continue
            day, month, year = (int(match.group(i)) for i in range(1, 4))
            waste_text = match.group(4).strip()
            waste_type = self._normalize_waste_type(waste_text)
            try:
                date_obj = datetime(year, month, day).date()
            except ValueError:
                continue
            if waste_type:
                entries.append({"date": date_obj, "type": waste_type})
        if not entries:
            raise ValueError(
                f"No collection dates found for street '{self._street}'. The website structure may have changed or no data is available for this address. Please verify your street name on https://abfall.wiener-neustadt.at/"
            )
        return sorted(entries, key=lambda x: x["date"])

    @staticmethod
    def _normalize_waste_type(waste_text: str) -> str:
        """Normalize waste type text to standard names.

        Args:
            waste_text: Raw waste type text from website

        Returns:
            Normalized waste type name; returns the original text if not recognized
        """
        waste_lower = waste_text.lower()
        if "bio" in waste_lower:
            return "Biotonne"
        if "christbaum" in waste_lower or "tannenbaum" in waste_lower:
            return "Christbaum"
        if "wertstoff" in waste_lower or "gelb" in waste_lower:
            return "Wertstoffe"
        if "papier" in waste_lower:
            return "Altpapier"
        if "kleider" in waste_lower or "textil" in waste_lower:
            return "Altkleider"
        if any(x in waste_lower for x in ["rest", "müll", "m�ll"]):
            return "Restmüll"
        return waste_text


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
