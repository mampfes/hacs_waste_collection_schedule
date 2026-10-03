"""Hillingdon's "Look up my collection day": a weekday, and a bank holiday table.

The council publishes no dates. Its ``ajaxlibrary`` JSON-RPC answers a UPRN with
the weekday the property is collected on and the rounds that run that day, and
the bank holiday page lists the days a collection moves (``Friday 25 December``
to ``Saturday 26 December``, no year). A source on this service composes the
three pieces::

    retrieve = BinDayRetriever()
    parse = BinDayParser()
    preprocess = WeeklyCollections(weeks=8)
    transform = RowTransformer(type_value_map={...})

The bank holiday page is optional: when it cannot be read the plain weekly
dates are returned, as the council's own look-up does.
"""

from __future__ import annotations

import datetime
import logging
import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import recurrence
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import Preprocessor

if TYPE_CHECKING:
    from collections.abc import Iterable

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import Response

_LOGGER = logging.getLogger(__name__)

API_URL = "https://www.hillingdon.gov.uk/apiserver/ajaxlibrary"
BANK_HOLIDAY_URL = "https://www.hillingdon.gov.uk/bank-holiday-collections"
REFERER = "https://www.hillingdon.gov.uk/article/1171/Look-up-my-collection-day"
METHOD = "Hillingdon.DatasourceQueries.alloy.GetBinCollectionDay"

_PARENTHESES = re.compile(r"\s*\(.*?\)")
_TRAILING_PARENTHESES = re.compile(r"\s*\(.*?\)\s*$")


class BinDayRetriever:
    """The weekday lookup for ``uprn``, then the bank holiday page.

    Returns the lookup response, followed by the bank holiday page when it could
    be fetched. A page that is down must not take the schedule with it, so only
    the lookup is allowed to fail the fetch.
    """

    def __init__(self, *, timeout: int = 10):
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> list[Response]:
        lookup = source.session.post(
            API_URL,
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": METHOD,
                "params": {"UPRN": source.params["uprn"]},
            },
            headers={"Referer": REFERER},
            timeout=self.timeout,
        )
        lookup.raise_for_status()
        responses = [lookup]
        try:
            holidays = source.session.get(BANK_HOLIDAY_URL, timeout=self.timeout)
            holidays.raise_for_status()
            responses.append(holidays)
        except Exception as error:
            _LOGGER.debug("Bank holiday page unavailable: %s", error)
        return responses


def revisions(markup: str, today: datetime.date) -> dict[datetime.date, datetime.date]:
    """``{normal date: revised date}`` from the bank holiday table's rows.

    Both columns read ``Wednesday 25 December`` with no year. The normal date
    takes the current year, or the next once it is more than 30 days past; the
    revised date follows it, rolling into the next year when it falls earlier
    in the calendar (``31 December`` moved to ``2 January``).
    """
    table = BeautifulSoup(markup, "html.parser").find("table")
    found: dict[datetime.date, datetime.date] = {}
    if table is None:
        return found
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        normal_text = _PARENTHESES.sub("", cells[0].get_text(strip=True)).strip()
        revised_text = cells[1].get_text(strip=True)
        year = today.year
        try:
            normal = _day_month(normal_text, year)
            if normal < today - datetime.timedelta(days=30):
                year += 1
                normal = _day_month(normal_text, year)
            revised = _day_month(revised_text, year)
            if revised < normal - datetime.timedelta(days=180):
                revised = _day_month(revised_text, year + 1)
        except ValueError:
            continue
        found[normal] = revised
    return found


def _day_month(text: str, year: int) -> datetime.date:
    """``Wednesday 25 December`` read in ``year`` (a year is needed for 29 February)."""
    return datetime.datetime.strptime(f"{text} {year}", "%A %d %B %Y").date()


class BinDayParser:
    """One record: the weekday, the rounds collected on it and the date moves."""

    def __call__(
        self, response: list[Response], source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        lookup, *pages = response
        uprn = source.params["uprn"] if source is not None else ""
        result = (lookup.json() or {}).get("result") or {}
        if not result.get("success"):
            raise SourceArgumentNotFound(
                "uprn",
                uprn,
                "No collection data found for this UPRN. Please verify it is correct.",
            )
        try:
            moves = revisions(pages[0].text, datetime.date.today()) if pages else {}
        except Exception as error:
            _LOGGER.debug("Bank holiday page not understood: %s", error)
            moves = {}
        return [
            {
                "day": result.get("collectionDay", ""),
                "rounds": result.get("collection") or [],
                "revisions": moves,
            }
        ]


class WeeklyCollections(Preprocessor):
    """Project the record's weekday into dates and apply its bank holiday moves.

    Each round is collected every week from the next occurrence of the weekday
    (today included) for ``weeks`` weeks. A date the bank holiday table moves is
    replaced by its revised date. The council appends a validity note to a round
    that is ending (``Garden Waste ( - 31/05/2026 23:59)``); it is dropped from
    the label.
    """

    def __init__(self, *, weeks: int = 8):
        self.weeks = weeks

    def __call__(
        self, records: Any, source: BaseSource | None = None
    ) -> Iterable[tuple[datetime.date, str]]:
        for record in records:
            weekday = recurrence.weekday(str(record["day"]))
            if weekday is None:
                continue
            start = recurrence.next_weekday(weekday)
            for round_name in record["rounds"]:
                label = _TRAILING_PARENTHESES.sub("", round_name).strip()
                for collection_date in recurrence.recurring(
                    start, recurrence.WEEKLY, self.weeks
                ):
                    yield (
                        record["revisions"].get(collection_date, collection_date),
                        label,
                    )
