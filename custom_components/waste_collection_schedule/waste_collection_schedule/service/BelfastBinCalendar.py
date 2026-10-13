"""BelfastBinCalendar retrieval and parsing, using the pipeline HTTP session."""

import logging
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import HtmlLabelledDates
from waste_collection_schedule.retrievers import RetrieverFunc, form_inputs

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
        state = form_inputs(
            soup, required=("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION")
        )
        _LOGGER.debug(f"Submitting postcode: {self._postcode}")
        postcode_data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": state["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": state["__VIEWSTATEGENERATOR"],
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "0",
            "__EVENTVALIDATION": state["__EVENTVALIDATION"],
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
        state = form_inputs(
            soup, required=("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION")
        )
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
            "__VIEWSTATE": state["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": state["__VIEWSTATEGENERATOR"],
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "0",
            "__EVENTVALIDATION": state["__EVENTVALIDATION"],
            "ctl00$MainContent$searchBy_radio": "P",
            "ctl00$MainContent$Street_textbox": "",
            "ctl00$MainContent$Postcode_textbox": self._postcode,
            "ctl00$MainContent$lstAddresses": uprn,
            "ctl00$MainContent$SelectAddress_button": "Select address",
        }
        response = session.post(API_URL, data=address_data, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(HtmlLabelledDates):
    """Configure the shared row parser for Belfast's four-column results."""

    def __init__(self):
        super().__init__(
            "#ItemsGrid tr:has(> td:nth-of-type(4)):not(:has(> td:nth-of-type(5)))",
            label="td:nth-of-type(1)",
            date="td:nth-of-type(4)",
            parse_date=date_parsers.for_format("%a %b %d %Y"),
        )

    def __call__(self, response: Any, source: BaseSource | None = None):
        if (
            BeautifulSoup(response.text, "html.parser").find("table", id="ItemsGrid")
            is None
        ):
            raise ValueError("Could not find bin collection schedule table")
        entries = super().__call__(response, source)
        if not entries:
            raise ValueError("No bin collection entries found")
        return entries
