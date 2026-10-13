"""WiganNeighbourhoodCalendar retrieval and parsing through the shared, verified HTTP session."""

import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

REGEX_ORDINALS = "(st|nd|rd|th)"


class _CalendarClient:
    _session: Any

    def __init__(self, postcode, uprn):
        self._postcode = str(postcode.upper())
        self._uprn = str(uprn).zfill(12)

    def get_asp_var(self, broth, id) -> str:
        asp_var = broth.find("input", {"id": id}).get("value")
        return asp_var

    def retrieve(self):
        s = self._session
        r0 = s.get("https://apps.wigan.gov.uk/MyNeighbourhood/")
        r0.raise_for_status()
        soup = BeautifulSoup(r0.text, "html.parser")
        payload = {
            "__VIEWSTATE": self.get_asp_var(soup, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": self.get_asp_var(soup, "__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": self.get_asp_var(soup, "__EVENTVALIDATION"),
            "ctl00$ContentPlaceHolder1$txtPostcode": self._postcode,
            "ctl00$ContentPlaceHolder1$btnPostcodeSearch": "Search",
        }
        r1 = s.post("https://apps.wigan.gov.uk/MyNeighbourhood/", data=payload)
        r1.raise_for_status()
        soup = BeautifulSoup(r1.text, features="html.parser")
        payload = {
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$lstAddresses",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": self.get_asp_var(soup, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": self.get_asp_var(soup, "__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": self.get_asp_var(soup, "__EVENTVALIDATION"),
            "ctl00$ContentPlaceHolder1$txtPostcode": self._postcode,
            "ctl00$ContentPlaceHolder1$lstAddresses": "UPRN" + self._uprn,
        }
        r2 = s.post("https://apps.wigan.gov.uk/MyNeighbourhood/", data=payload)
        r2.raise_for_status()
        return r2

    def parse(self, r2):
        soup = BeautifulSoup(r2.text, features="html.parser")
        bin_collections = soup.findAll("div", {"class": "BinsRecycling"})
        entries = []
        for bin in bin_collections:
            waste_type = bin.find("h2").text
            waste_date = bin.find("div", {"class": "dateWrapper-next"}).get_text(
                strip=True
            )
            waste_date = re.compile(REGEX_ORDINALS).sub("", waste_date.split("day")[1])
            waste_date = datetime.strptime(waste_date, "%d%b%Y").date()
            entries.append({"date": waste_date, "type": waste_type})
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
