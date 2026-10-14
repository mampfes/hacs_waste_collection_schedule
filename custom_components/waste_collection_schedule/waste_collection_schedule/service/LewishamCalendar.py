"""LewishamCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import datetime
import hashlib
import logging
import re
from typing import Any

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)
BASE_URL = "https://lewisham.gov.uk"
ADDRESS_SEARCH_URL = "https://lewisham.gov.uk/api/AddressFinder"
DATE_REGEX = "(\\d{2}/\\d{2}/\\d{4})"
DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
ID_SEPERATOR = "-----------------------------{rand_id}"
PAYLOAD_SECTION_TEMPLATE = (
    ID_SEPERATOR
    + '\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
)
HEADERS = {"User-Agent": "Mozilla/5.0"}


class InsufficientDataError(Exception):
    pass


class _CalendarClient:
    _session: Any

    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._post_code = post_code
        self._number = number
        self._name = name
        self._uprn = uprn

    def get_uprn(self) -> None:
        if not self._uprn:
            p = {"postcodeOrStreet": self._post_code}
            r = self._session.post(ADDRESS_SEARCH_URL, params=p, headers=HEADERS)
            r.raise_for_status()
            addresses = r.json()
            if self._name:
                self._uprn = next(
                    x["Uprn"]
                    for x in addresses
                    if x["Title"].upper().startswith(self._name.upper())
                )
            elif self._number:
                self._uprn = next(
                    x["Uprn"]
                    for x in addresses
                    if x["Title"].startswith(str(self._number))
                )
            if not self._uprn:
                raise ValueError(
                    f"Could not find address {self._post_code} {self._number}{self._name}"
                )

    def retrieve(self) -> Any:
        if not self._uprn:
            self.get_uprn()
        s = self._session
        r = s.get(
            "https://lewisham.gov.uk/myservices/recycling-and-rubbish/your-bins/collection",
            headers=HEADERS,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form_div = soup.find("div", {"class": "address-finder"})
        if not isinstance(form_div, Tag):
            raise ValueError("Could not find address form")
        form = form_div.find_parent("form")
        if not isinstance(form, Tag):
            raise ValueError("Could not find address form")
        action = form.get("action")
        if not isinstance(action, str) or not action:
            raise ValueError("Could not find form action")
        if action.startswith("/"):
            action = BASE_URL + action
        inputs = form.find_all("input")
        rand_id = hashlib.sha256(str(self._uprn).encode()).hexdigest()[:32]
        payload = ""
        for input in inputs:
            name = input.get("name")
            value = input.get("value")
            if isinstance(name, str) and name:
                if name.endswith("Value"):
                    value = self._uprn
                payload += PAYLOAD_SECTION_TEMPLATE.format(
                    rand_id=rand_id, name=name, value=value
                )
        payload += ID_SEPERATOR.format(rand_id=rand_id) + "--\r\n"
        headers = {
            **HEADERS,
            "Content-Type": f"multipart/form-data; boundary=---------------------------{rand_id}",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
        }
        r = s.post(action, data=payload, headers=headers)
        r.raise_for_status()
        url = r.text.split("='")[-1].split("';")[0]
        if not url:
            raise ValueError("Could not find collection URL")
        if url.startswith("/"):
            url = BASE_URL + url
        r = s.get(url, headers=HEADERS)
        r.raise_for_status()
        return r

    def parse(self, r):
        soup = BeautifulSoup(r.text, "html.parser")
        heading = soup.find("h2", text="When your bins are collected:")
        if not heading:
            raise ValueError("Could not find collection heading")
        entries: list[dict] = []
        waste_type: str | None = None
        frequency: str | None = None
        week_day: str | None = None
        date: datetime.date | None = None
        container = heading.parent
        if container is None:
            raise ValueError("Could not find collection container")
        for sibling in container.contents:
            if isinstance(sibling, Tag) and sibling.name == "strong":
                if waste_type is not None:
                    try:
                        entries.extend(
                            self._calculate_collections(
                                waste_type, frequency, week_day, date
                            )
                        )
                    except InsufficientDataError as e:
                        _LOGGER.warning(
                            f"Could not calculate collection got exception: {e}"
                        )
                    waste_type = None
                    frequency = None
                    week_day = None
                    date = None
                waste_type = sibling.text.strip()
            if isinstance(sibling, Tag) and sibling.name == "span":
                frequency = sibling.text
            if isinstance(sibling, NavigableString):
                for day in DAYS:
                    if day.lower() in sibling.text.lower():
                        week_day = day
                        break
                if result := re.search(DATE_REGEX, sibling.text):
                    date = datetime.datetime.strptime(
                        result.group(1), "%d/%m/%Y"
                    ).date()
        try:
            entries.extend(
                self._calculate_collections(waste_type, frequency, week_day, date)
            )
        except InsufficientDataError as e:
            _LOGGER.warning(f"Could not calculate collection got exception: {e}")
        return entries

    def _calculate_collections(
        self,
        waste_type: str | None,
        frequency: str | None,
        week_day: str | None,
        date: datetime.date | None,
    ) -> list[dict]:
        if waste_type is None:
            raise InsufficientDataError("Waste type not provided")
        if frequency not in ("WEEKLY", "FORTNIGHTLY"):
            raise InsufficientDataError("Frequency not provided")
        if week_day is None:
            raise InsufficientDataError("Week day not provided")
        if frequency == "FORTNIGHTLY" and date is None:
            raise InsufficientDataError("Date not provided")
        entries = []
        collection_dates: list[datetime.date] = []
        if date is None:
            d = datetime.date.today()
            date = d + datetime.timedelta(
                (DAYS.index(week_day.upper()) + 1 - d.isoweekday()) % 7
            )
        if frequency == "FORTNIGHTLY":
            collection_dates = [date + datetime.timedelta(i * 14) for i in range(5)]
        else:
            collection_dates = [date + datetime.timedelta(i * 7) for i in range(10)]
        for collection_date in collection_dates:
            entries.append({"date": collection_date, "type": waste_type})
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
