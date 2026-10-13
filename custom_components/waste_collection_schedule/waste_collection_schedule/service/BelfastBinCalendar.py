"""BelfastBinCalendar retrieval and parsing, using the pipeline HTTP session."""

import logging
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)

API_URL = "https://online.belfastcity.gov.uk/find-bin-collection-day/Default.aspx"
REQUEST_TIMEOUT = 30


class _CalendarClient:
    _session: Any
    """Belfast City Council waste collection source."""

    def __init__(self, postcode: str, uprn: str | None = None):
        """
        Initialize the source.

        Args:
            postcode: Postcode to search for (e.g., "BT1 5GS")
            uprn: Optional UPRN (Unique Property Reference Number) if known.
                  If not provided, the first address at the postcode will be used.
        """
        self._postcode = postcode.strip().upper()
        self._uprn = uprn

    def retrieve(self):
        """Fetch waste collection schedule."""
        session = self._session
        _LOGGER.debug(f"Fetching initial page for postcode: {self._postcode}")
        response = session.get(API_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        viewstate_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})[
            "value"
        ]
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        _LOGGER.debug(f"Submitting postcode: {self._postcode}")
        postcode_data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstate_generator,
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "0",
            "__EVENTVALIDATION": event_validation,
            "ctl00$MainContent$searchBy_radio": "P",
            "ctl00$MainContent$Street_textbox": "",
            "ctl00$MainContent$Postcode_textbox": self._postcode,
            "ctl00$MainContent$AddressLookup_button": "Find address",
        }
        response = session.post(API_URL, data=postcode_data, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        error_msg = soup.find("span", {"id": "lblPostcodeError"})
        if error_msg and error_msg.get("style") != "display:none":
            raise ValueError(f"Error from website: {error_msg.get_text(strip=True)}")
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        viewstate_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})[
            "value"
        ]
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        address_select = soup.find("select", {"id": "lstAddresses"})
        if not address_select:
            raise ValueError(f"No addresses found for postcode: {self._postcode}")
        if self._uprn:
            uprn = self._uprn
            _LOGGER.debug(f"Using provided UPRN: {uprn}")
        else:
            options = address_select.find_all("option")
            valid_options = [
                opt
                for opt in options
                if not opt.get_text(strip=True).startswith("Select")
            ]
            if not valid_options:
                raise ValueError(
                    f"No valid addresses found for postcode: {self._postcode}"
                )
            uprn = valid_options[0]["value"]
            address_text = valid_options[0].get_text(strip=True)
            _LOGGER.debug(f"Using first address: {address_text} (UPRN: {uprn})")
        _LOGGER.debug(f"Fetching bin collection schedule for UPRN: {uprn}")
        address_data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstate_generator,
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "0",
            "__EVENTVALIDATION": event_validation,
            "ctl00$MainContent$searchBy_radio": "P",
            "ctl00$MainContent$Street_textbox": "",
            "ctl00$MainContent$Postcode_textbox": self._postcode,
            "ctl00$MainContent$lstAddresses": uprn,
            "ctl00$MainContent$SelectAddress_button": "Select address",
        }
        response = session.post(API_URL, data=address_data, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response

    def parse(self, response):
        return self._parse_schedule(response.text)

    def _parse_schedule(self, html: str):
        """Parse the bin collection schedule from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"id": "ItemsGrid"})
        if not table:
            raise ValueError("Could not find bin collection schedule table")
        entries = []
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) != 4:
                continue
            bin_type = cols[0].get_text(strip=True)
            next_collection = cols[3].get_text(strip=True)
            try:
                next_collection = re.sub("\\s+", " ", next_collection)
                date = datetime.strptime(next_collection, "%a %b %d %Y").date()
                entries.append({"date": date, "type": bin_type})
                _LOGGER.debug(f"Added collection: {bin_type} on {date}")
            except ValueError as e:
                _LOGGER.warning(f"Could not parse date '{next_collection}': {e}")
                continue
        if not entries:
            raise ValueError("No bin collection entries found")
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
