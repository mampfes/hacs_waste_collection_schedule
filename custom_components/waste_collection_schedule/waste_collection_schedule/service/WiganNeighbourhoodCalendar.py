"""WiganNeighbourhoodCalendar retrieval and parsing through the shared, verified HTTP session."""

import re
from datetime import date
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import RetrieverFunc, form_inputs

REGEX_ORDINALS = "(st|nd|rd|th)"


class _CalendarClient:
    _session: Any

    def __init__(self, postcode, uprn):
        self._postcode = str(postcode.upper())
        self._uprn = str(uprn).zfill(12)

    def retrieve(self):
        s = self._session
        r0 = s.get("https://apps.wigan.gov.uk/MyNeighbourhood/")
        r0.raise_for_status()
        soup = BeautifulSoup(r0.text, "html.parser")
        state = form_inputs(
            soup, required=("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION")
        )
        payload = {
            "__VIEWSTATE": state["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": state["__VIEWSTATEGENERATOR"],
            "__EVENTVALIDATION": state["__EVENTVALIDATION"],
            "ctl00$ContentPlaceHolder1$txtPostcode": self._postcode,
            "ctl00$ContentPlaceHolder1$btnPostcodeSearch": "Search",
        }
        r1 = s.post("https://apps.wigan.gov.uk/MyNeighbourhood/", data=payload)
        r1.raise_for_status()
        soup = BeautifulSoup(r1.text, features="html.parser")
        state = form_inputs(
            soup, required=("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION")
        )
        payload = {
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$lstAddresses",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": state["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": state["__VIEWSTATEGENERATOR"],
            "__EVENTVALIDATION": state["__EVENTVALIDATION"],
            "ctl00$ContentPlaceHolder1$txtPostcode": self._postcode,
            "ctl00$ContentPlaceHolder1$lstAddresses": "UPRN" + self._uprn,
        }
        r2 = s.post("https://apps.wigan.gov.uk/MyNeighbourhood/", data=payload)
        r2.raise_for_status()
        return r2


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


def collection_date(*values: str) -> date:
    """Wigan joins ordinal day, month and year without spaces."""
    return date_parsers.for_format("%d%b%Y")(re.sub(REGEX_ORDINALS, "", values[-1]))
