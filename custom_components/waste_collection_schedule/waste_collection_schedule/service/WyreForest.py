"""Wyre Forest District Council's "rubbish and recycling query" pages.

``forms.wyreforestdc.gov.uk/querybin.asp`` answers a street and town with the
property's collection weekday, and a "Next Rubbish Collection" / "Next
Recycling Collection" column naming a relative day ("This Thursday", "Next
Thursday", "Today", "Tomorrow"). Rubbish and recycling alternate fortnightly.

Garden waste lives on a second form, ``GardenWasteChecker/Home/Details``,
keyed by the customer number. It names only a weekday and says the brown bin
is collected "on the same week as your rubbish bin collection", so its dates
are derived from the rubbish week.

:class:`WyreForestRetriever` issues the one or two requests and
:class:`WyreForestParser` reads them into ``(date, label)`` rows: five
fortnightly collections for each service, labelled ``"rubbish"``,
``"recycling"`` and ``"garden waste"``.
"""

import datetime
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import date_parsers
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.recurrence import weekday

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

WASTE_URL = "https://forms.wyreforestdc.gov.uk/querybin.asp"
GARDEN_URL = "https://forms.wyreforestdc.gov.uk/GardenWasteChecker/Home/Details"

GARDEN_LABEL = "garden waste"

#: How many fortnightly collections are projected for each service.
COLLECTIONS = 5
FORTNIGHT = datetime.timedelta(days=14)

_BIN_TYPE = re.compile(r"Next (.*?) Collection")
_THIS_OR_NEXT = re.compile(r"(This|Next) (.*?)$", re.IGNORECASE)
_GARDEN_DAY = re.compile(
    r"collection is on a\s*(.*?)\s*and will be collected on the same week as"
)
_GARDEN_SAME_WEEK_AS = re.compile(
    r"collected on the same week as your\s*(.*?)\s*(bin)?\s*collection"
)
_ABSOLUTE_DATE_FORMATS = (
    date_parsers.for_format("%d %B %Y"),
    date_parsers.for_format("%d %b %Y"),
)


class WyreForestRetriever:
    """The rubbish page, plus the garden waste page when a customer is given."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def __call__(self, source: "BaseSource") -> list[Any]:
        params = source.params
        session = source.session
        responses = [
            session.post(
                WASTE_URL,
                params={
                    "txtStreetName": str(params["street"]).upper().strip(),
                    "select": "yes",
                    "town": str(params["town"]).upper().strip(),
                },
                timeout=self.timeout,
            )
        ]
        customer = str(params.get("garden_cutomer") or "").strip()
        if customer:
            responses.append(
                session.post(
                    GARDEN_URL, data={"CUST_No": customer}, timeout=self.timeout
                )
            )
        for response in responses:
            response.raise_for_status()
        return responses


def _relative_date(text: str) -> datetime.date:
    """``Today``, ``Tomorrow``, ``This Thursday``, ``Next Thursday`` or a date."""
    today = datetime.date.today()
    text = text.strip()
    lowered = text.lower()
    if lowered == "today":
        return today
    if lowered == "tomorrow":
        return today + datetime.timedelta(days=1)
    match = _THIS_OR_NEXT.match(text)
    if match:
        index = weekday(match.group(2))
        if index is None:
            raise ValueError(f"Invalid weekday: {text}")
        start = today + datetime.timedelta(
            days=7 if match.group(1).lower() == "next" else 0
        )
        return start + datetime.timedelta(days=(index - start.weekday()) % 7)
    for parse in _ABSOLUTE_DATE_FORMATS:
        try:
            return parse(text)
        except ValueError:
            continue
    raise ValueError(f"Invalid weekday: {text}")


def _fortnightly(first: datetime.date) -> Iterable[datetime.date]:
    return (first + i * FORTNIGHT for i in range(COLLECTIONS))


class WyreForestParser:
    """``(date, label)`` rows from the retriever's one or two responses."""

    def _garden(
        self, response: Any, customer: Any, type_to_day: dict[str, str]
    ) -> list[tuple[datetime.date, str]]:
        text = BeautifulSoup(response.text, "html.parser").text
        day = _GARDEN_DAY.search(text)
        same_week_as = _GARDEN_SAME_WEEK_AS.search(text)
        if not day or not same_week_as:
            raise SourceArgumentNotFound("garden_cutomer", customer)
        index = weekday(day.group(1))
        reference = type_to_day.get(same_week_as.group(1).lower())
        if index is None or reference is None:
            raise ValueError(
                f"Could not find garden waste collection days: {day} {same_week_as}"
            )
        rubbish_day = _relative_date(reference)
        monday = rubbish_day - datetime.timedelta(days=rubbish_day.weekday())
        return [
            (d, GARDEN_LABEL)
            for d in _fortnightly(monday + datetime.timedelta(days=index))
        ]

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> list[tuple[datetime.date, str]]:
        responses = response if isinstance(response, list) else [response]
        soup = BeautifulSoup(responses[0].text, "html.parser")
        header = soup.find("p", string="Collection Day")
        table = header.find_parent("table") if header else None
        if table is None:
            if "no addresses matching" in soup.text.lower():
                params = source.params if source else {}
                raise SourceArgumentNotFound(
                    "street", f"{params.get('street')}, {params.get('town')}"
                )
            raise ValueError("Could not find collection day table")
        rows = table.find_all("tr")
        if len(rows) != 2:
            raise ValueError("Could not find collection day rows")
        headings = [td.text.strip() for td in rows[0].find_all("td")]
        values = [td.text.strip() for td in rows[1].find_all("td")]

        type_to_day: dict[str, str] = {}
        out: list[tuple[datetime.date, str]] = []
        for heading, value in zip(headings, values, strict=False):
            match = _BIN_TYPE.match(heading)
            if match is None:
                continue
            label = match.group(1).lower()
            type_to_day[label] = value
            out.extend((d, label) for d in _fortnightly(_relative_date(value)))
        if len(responses) > 1:
            customer = source.params.get("garden_cutomer") if source else None
            out.extend(self._garden(responses[1], customer, type_to_day))
        return out
