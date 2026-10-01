"""The i-web municipal CMS's "Regelmässige Abfuhr" collections (Swiss municipalities).

Next to the dated collection table that :mod:`.IWeb` reads, some i-web sites list
*regular* collections in a second table, ``#regulaeresammlungen``. These have no
dates: each links to a detail page that states the rhythm in prose ("findet
wöchentlich am Dienstag statt"), and for a seasonal collection its first and last
day ("erstmals am 2. März und letztmals am 30. November 2026")::

    retrieve = abfalldaten_with_regular_retriever("https://www.example.ch/abfalldaten")
    parse = AbfalldatenRegularParser()
    preprocess = AbfalldatenRegularRows()
    transform = ICSTransformer(type_value_map={...})

``retrieve`` returns the events page followed by one detail page per regular
collection; the parser turns them into the dated records of the events table
plus one weekly descriptor per regular collection, and the preprocessor projects
the weekly collections (within their season) over the next ``horizon_days`` and
yields ``(date, name)`` rows alongside the dated ones. The weekday and season are
read from the live prose on every fetch.
"""

import datetime
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import recurrence
from waste_collection_schedule.parsers import (
    AttributeJsonParser,
    HtmlTextParser,
    Parser,
)
from waste_collection_schedule.preprocessors import (
    Preprocessor,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.service.IWeb import AbfalldatenRows, abfalldaten_parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_WEEKDAY = re.compile(r"wöchentlich\s+am\s+(\w+)")
_SEASON = re.compile(
    r"erstmals am (\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)"
    r".*?"
    r"letztmals am (\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)",
    re.DOTALL,
)

_REGULAR_TABLE = AttributeJsonParser(
    "table#regulaeresammlungen[data-entities]",
    "data-entities",
    "data",
    require_keys=("name",),
)


def regular_links(events: Any) -> list[tuple[str, str]]:
    """``(name, detail URL)`` of each regular collection on the events page."""
    links = []
    for record in _REGULAR_TABLE(events):
        anchor = BeautifulSoup(record.get("name", ""), "html.parser").find("a")
        if anchor is not None and anchor.get("href"):
            links.append(
                (anchor.get_text(strip=True), urljoin(events.url, str(anchor["href"])))
            )
    return links


def abfalldaten_with_regular_retriever(url: str) -> FanOutRetriever:
    """The events page (first response), then each regular collection's page."""
    detail = Request(lambda target, _events, **_: target)
    return FanOutRetriever(
        prepare=Lookup(url, pick=lambda response, **_: response),
        targets=lambda source, events: [
            events,
            *(link for _, link in regular_links(events)),
        ],
        fetch=lambda source, target, events: (
            events if target is events else detail(source, target, events)
        ),
    )


def _season(text: str) -> tuple[int, int, int, int] | None:
    """``(start month, start day, end month, end day)``; None if all year."""
    match = _SEASON.search(text)
    if match is None:
        return None
    start_day, start_month, end_day, end_month = match.groups()
    start, end = recurrence.month(start_month), recurrence.month(end_month)
    if start is None or end is None:
        return None
    return start, int(start_day), end, int(end_day)


class AbfalldatenRegularParser(Parser["list[dict[str, Any]]"]):
    """Records for the dated table (``kind="special"``) and the regular ones.

    A regular collection whose page names no recurring weekday is skipped rather
    than guessed.
    """

    def __call__(
        self, responses: Any, source: "BaseSource | None" = None
    ) -> "list[dict[str, Any]]":
        events, *details = responses
        records: list[dict[str, Any]] = [
            {"kind": "special", **record}
            for record in abfalldaten_parser()(events, source)
        ]
        text_parser = HtmlTextParser()
        for (name, _), detail in zip(regular_links(events), details, strict=True):
            text = text_parser(detail, source)
            match = _WEEKDAY.search(text)
            weekday = recurrence.weekday(match.group(1)) if match else None
            if weekday is None:
                continue
            records.append(
                {
                    "kind": "regular",
                    "name": name,
                    "weekday": weekday,
                    "season": _season(text),
                }
            )
        return records


class AbfalldatenRegularRows(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """``(date, name)`` rows: the dated collections, plus the weekly ones projected.

    Args:
        horizon_days: how far ahead the weekly collections are generated.
    """

    def __init__(self, *, horizon_days: int = 400):
        self.horizon_days = horizon_days

    def _describe(self, record: dict, source: Any = None) -> Iterable[Schedule]:
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=self.horizon_days)
        start = recurrence.next_weekday(record["weekday"], on_or_after=today)
        season = record["season"]
        if season is None:
            yield Schedule(
                record["name"],
                start,
                recurrence.WEEKLY,
                not_before=today,
                until=horizon,
            )
            return
        start_month, start_day, end_month, end_day = season
        for year in (today.year, today.year + 1):
            first = max(today, datetime.date(year, start_month, start_day))
            last = min(horizon, datetime.date(year, end_month, end_day))
            if first <= last:
                yield Schedule(
                    record["name"],
                    start,
                    recurrence.WEEKLY,
                    not_before=first,
                    until=last,
                )

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        special = [r for r in records if r["kind"] == "special"]
        regular = [r for r in records if r["kind"] == "regular"]
        yield from AbfalldatenRows()(special, source)
        yield from RecurrenceExpander(self._describe)(regular, source)
