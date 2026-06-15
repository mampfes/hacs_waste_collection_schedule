"""Standard response parsers for waste collection sources.

Each parser is a typed callable class that integrates with the
retrieve → parse → transform pipeline in BaseSource. A parser turns a raw
HTTP response into an iterable of records (the shape depends on the parser).

Simple parsers (instantiate and assign):

    parse = parsers.JsonParser()    # response.json() — list or dict of records
    parse = parsers.IcsParser()     # list of (date, summary) tuples

Configurable parsers (pass arguments to the constructor):

    parse = parsers.JsonParser("collections")  # response.json()["collections"]
    parse = parsers.HtmlParser("tr", skip=1)    # <tr> elements, header skipped
"""

import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Protocol,
    Tuple,
    TypeAlias,
    TypeVar,
)

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.service.ICS import IcsEvent

if TYPE_CHECKING:
    import requests
    from curl_cffi import requests as _cffi_requests

    Response: TypeAlias = "requests.Response | _cffi_requests.Response"
else:
    Response = object

T = TypeVar("T", covariant=True)


class Parser(Protocol[T]):
    """A callable that converts an HTTP response into records of type T."""

    def __call__(self, response: Response) -> T: ...  # noqa: E704


class JsonParser(Parser[Any]):
    """Parse response as JSON, optionally drilling into a nested key path.

    With no arguments, returns the top-level parsed value::

        parse = parsers.JsonParser()          # response.json()

    With one or more keys, walks the parsed value before returning::

        parse = parsers.JsonParser("collections")     # response.json()["collections"]
        parse = parsers.JsonParser("data", "items")   # response.json()["data"]["items"]

    If the response is already a list at the top level, omit keys entirely.
    """

    def __init__(self, *keys: str):
        self.keys = keys

    def __call__(self, response: Response) -> Any:
        data = response.json()
        for key in self.keys:
            data = data[key]
        return data


class TextParser(Parser[str]):
    """Return response as plain text."""

    def __call__(self, response: Response) -> str:
        return response.text


class HtmlParser(Parser[List[Tag]]):
    """Parse response as HTML and select elements by CSS selector.

    Use with HtmlTransformer. Selects all elements matching ``selector``
    (CSS selector syntax) and skips the first ``skip`` results (handy for
    stripping header rows)::

        parse = parsers.HtmlParser("tr", skip=1)   # all rows, skip header
        parse = parsers.HtmlParser("ul.bins > li") # list items

    Each element is passed individually to the transformer.

    Args:
        selector: CSS selector string passed to BeautifulSoup.select().
        skip:     Number of leading elements to drop (default 0).
    """

    def __init__(self, selector: str, skip: int = 0):
        self.selector = selector
        self.skip = skip

    def __call__(self, response: Response) -> List[Tag]:
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.select(self.selector)[self.skip :]


class IcsParser(Parser[List[Tuple[datetime.date, str]]]):
    """Parse response as an iCalendar feed.

    Returns a list of (date, summary) tuples for all events in the next year.
    Use this with the default retriever and an ICSTransformer::

        parse = parsers.IcsParser()
        transformer = ICSTransformer(type_value_map={...})
    """

    def __call__(self, response: Response) -> List[Tuple[datetime.date, str]]:
        from waste_collection_schedule.service.ICS import ICS

        return ICS().convert(response.text)


class IcsEventsParser(Parser[List[IcsEvent]]):
    """Parse response as an iCalendar feed, exposing full event fields.

    Like :class:`IcsParser`, but returns ``IcsEvent(date, title, location,
    description)`` records instead of bare ``(date, summary)`` tuples. Use this
    with ``classify()`` when the source must inspect the ICS ``LOCATION`` or
    ``DESCRIPTION`` fields — for example to filter events by collection route::

        parse = parsers.IcsEventsParser()

        def classify(self, record) -> Collection | None:
            # record.title / record.location / record.description available
            return Collection(date=record.date, waste_type=...)
    """

    def __call__(self, response: Response) -> List[IcsEvent]:
        from waste_collection_schedule.service.ICS import ICS

        return ICS().convert_events(response.text)
