"""EnvironmentFirstCalendar retrieval and parsing through the shared, verified HTTP session."""

import logging
from typing import Any

from bs4 import BeautifulSoup
from dateutil.parser import parse

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

TYPE_LABELS = ("RUBBISH", "RECYCLING", "GARDEN WASTE")

_LOGGER = logging.getLogger(__name__)


class _CalendarClient:
    _session: Any

    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._uprn = uprn
        self._post_code = post_code
        self._number = str(number) if number is not None else None
        self._name = name

    def retrieve(self):
        s = self._session
        if self._uprn:
            r = s.get(f"https://environmentfirst.co.uk/house.php?uprn={self._uprn}")
            responseContent = r.text
        elif self._post_code and self._number:
            payload = {
                "property_no": self._number,
                "property_name": "",
                "street": "",
                "postcode": self._post_code,
            }
            r = s.post("https://environmentfirst.co.uk/results.php", data=payload)
            responseContent = r.text
        elif self._post_code and self._name:
            payload = {
                "property_no": "",
                "property_name": self._name,
                "street": "",
                "postcode": self._post_code,
            }
            r = s.post("https://environmentfirst.co.uk/results.php", data=payload)
            responseContent = r.text
            soup = BeautifulSoup(responseContent, "html.parser")
            table = soup.find("table")
            if table is None:
                raise ValueError("Could not find address results table")
            for row in table.find_all("tr")[1:]:
                if self._name in row.text:
                    for item in row("a", href=True):
                        href = item.get("href")
                        if not isinstance(href, str) or "=" not in href:
                            raise ValueError(
                                "Address result contains no property identifier"
                            )
                        self._uprn = href.split("=", 1)[1]
            r = s.get(f"https://environmentfirst.co.uk/house.php?uprn={self._uprn}")
            responseContent = r.text
        else:
            raise ValueError(
                "You need to specify either (uprn) or (post_code and (number or name))"
            )
        r.raise_for_status()
        return responseContent

    def parse(self, responseContent):
        entries = []
        soup = BeautifulSoup(responseContent, "html.parser")
        x = soup.find_all("p")
        for i in x[1:-1]:
            if " day " in i.text:
                for round_type in TYPE_LABELS:
                    if round_type in i.text.upper():
                        entries.append(
                            {
                                "date": parse(str.split(i.text, ":")[1]).date(),
                                "type": round_type,
                            }
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
