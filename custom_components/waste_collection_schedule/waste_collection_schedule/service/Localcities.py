"""localcities.ch waste calendars, Swiss municipalities.

localcities.ch publishes a municipality's collection calendar as one server-rendered
page, ``/de/entsorgung/<municipality>/<id>``. It lists the coming collections
grouped by month::

    <div data-js-result-list>
      <h1 class="calendar-list__headline">Oktober <span>2026</span></h1>
      <div class="row">
        <div class="waste-calender-list__date"><h2>13.10</h2> ...</div>
        <div class="waste-calendar-list-item-small list-calendar-item--waste-paper">
          <img alt="Altpapier"> Hegnau
        </div>
        ...

A date is ``DD.MM`` (the year is in the month heading before it, and "Heute" /
"Morgen" stand for today and tomorrow), an item is one waste type (the ``alt`` text
of its icon) with the zone, locality or district it applies to as its text (empty for
a municipality without zones). A longer calendar continues on ``?page=N``, announced
by a "load more" element carrying the next page number.

:func:`calendar_retriever` fetches the pages (optionally with further pages of the
municipality's own site, whose answers the source parses itself), :class:`CalendarParser`
reads them into :class:`Entry` rows, :class:`Combined` joins parsers over the same
responses and :class:`PlaceRows` keeps the rows of one zone.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Iterable, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.preprocessors import Preprocessor

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

BASE_URL = "https://www.localcities.ch/de/entsorgung"
_MAX_PAGES = 20


class Entry(NamedTuple):
    """One collection: the day, the waste type and the zone it applies to."""

    date: datetime.date
    label: str
    place: str


def calendar_url(municipality: str, municipality_id: Any) -> str:
    """The calendar page of a municipality, from its URL slug and id."""
    return (
        f"{BASE_URL}/{str(municipality).strip().lower()}/{str(municipality_id).strip()}"
    )


def _next_page(soup: BeautifulSoup) -> int | None:
    element = soup.find(attrs={"data-js-results-load-more-next-page": True})
    if element is None:
        return None
    value = element.get("data-js-results-load-more-next-page")
    if isinstance(value, list):
        value = value[0] if value else None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


class CalendarRetriever:
    """The pages of a calendar, and optionally further URLs, as a list of responses.

    Args:
        url: the calendar page, a literal or ``callable(**source.params)``.
        also: further URLs fetched first (a callable or literal each), for a
            source that combines the calendar with the municipality's own data.
    """

    def __init__(
        self,
        url: Callable[..., str] | str,
        also: Sequence[Callable[..., str] | str] = (),
    ):
        self.url = url
        self.also = tuple(also)

    def __call__(self, source: BaseSource) -> list[Any]:
        def resolve(value: Callable[..., str] | str) -> str:
            return value(**source.params) if callable(value) else value

        responses = [source.session.get(resolve(u), timeout=30) for u in self.also]
        url = resolve(self.url)
        page = 1
        while page <= _MAX_PAGES:
            response = source.session.get(
                url, params={"page": page} if page > 1 else None, timeout=30
            )
            response.raise_for_status()
            responses.append(response)
            following = _next_page(BeautifulSoup(response.text, "html.parser"))
            if following is None or following <= page:
                break
            page = following
        for response in responses[: len(self.also)]:
            response.raise_for_status()
        return responses


def calendar_retriever(
    url: Callable[..., str] | str, also: Sequence[Callable[..., str] | str] = ()
) -> CalendarRetriever:
    """A :class:`CalendarRetriever` for the calendar at ``url``."""
    return CalendarRetriever(url, also)


class CalendarParser(Parser["list[Entry]"]):
    """:class:`Entry` rows from a calendar page; any other page gives ``[]``."""

    def __call__(self, response: Any, source: BaseSource | None = None) -> list[Entry]:
        soup = BeautifulSoup(response.text, "html.parser")
        result_list = soup.find("div", attrs={"data-js-result-list": True})
        if result_list is None:
            return []
        today = datetime.date.today()
        year = today.year
        entries: list[Entry] = []
        for child in result_list.find_all(recursive=False):
            classes = child.get("class") or []
            if child.name == "h1" and any(
                "calendar-list__headline" in c for c in classes
            ):
                span = child.find("span")
                if span is not None and span.get_text(strip=True).isdigit():
                    year = int(span.get_text(strip=True))
                continue
            date_col = child.find("div", class_="waste-calender-list__date")
            heading = date_col.find(["h2", "h3"]) if date_col is not None else None
            if heading is None:
                continue
            text = heading.get_text(strip=True)
            if text == "Heute":
                day = today
            elif text == "Morgen":
                day = today + datetime.timedelta(days=1)
            else:
                try:
                    day = datetime.datetime.strptime(
                        f"{text}.{year}", "%d.%m.%Y"
                    ).date()
                except ValueError:
                    continue
            for item in child.find_all(
                "div",
                class_=lambda c: bool(c) and "waste-calendar-list-item-small" in c,
            ):
                image = item.find("img", alt=True)
                if image is None or not str(image["alt"]).strip():
                    continue
                entries.append(
                    Entry(day, str(image["alt"]).strip(), item.get_text(strip=True))
                )
        return entries


class Combined(Parser["list[Any]"]):
    """The records of several parsers over every response, concatenated.

    For the response list of a :class:`CalendarRetriever` with ``also``: each parser
    reads the pages it knows and answers ``[]`` for the others.
    """

    def __init__(self, *parsers: Parser):
        self.parsers = parsers

    def __call__(self, response: Any, source: BaseSource | None = None) -> list[Any]:
        responses = [response] if hasattr(response, "status_code") else response
        records: list[Any] = []
        for item in responses:
            for parser in self.parsers:
                records.extend(parser(item, source))
        return records


class PlaceRows(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """``(date, label)`` rows of the zone a source asks for.

    Rows are :class:`Entry` or plain ``(date, label)`` pairs; for a pair the label is
    also its place.

    Args:
        param: the ``source.params`` field naming the zone. Empty or missing keeps
            every row. A zone no row has raises with the zones that exist.
        match: instead of ``param``, ``callable(place, source) -> bool``.
    """

    def __init__(
        self,
        param: str | None = None,
        *,
        match: Callable[[str, Any], bool] | None = None,
    ):
        self.param = param
        self.match = match

    def __call__(
        self, records: Iterable[Any], source: BaseSource | None = None
    ) -> Iterable[tuple[datetime.date, str]]:
        wanted = None
        if self.param is not None and source is not None:
            wanted = str(source.params.get(self.param) or "").strip() or None
        rows = [(r[0], r[1], r[2] if len(r) > 2 else r[1]) for r in records]
        kept = [
            (day, label)
            for day, label, place in rows
            if (self.match is not None and self.match(place, source))
            or (self.match is None and (wanted is None or place == wanted))
        ]
        if not kept and wanted is not None and rows:
            raise SourceArgumentNotFoundWithSuggestions(
                self.param, wanted, sorted({place for _, _, place in rows})
            )
        return kept
