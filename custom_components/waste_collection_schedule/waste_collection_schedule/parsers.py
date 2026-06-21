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
    Protocol,
    TypeAlias,
    TypeVar,
)

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule.service.ICS import IcsEvent

if TYPE_CHECKING:
    import requests
    from curl_cffi import requests as _cffi_requests

    from waste_collection_schedule.base_source import BaseSource

    Response: TypeAlias = "requests.Response | _cffi_requests.Response"
else:
    Response = object

T = TypeVar("T", covariant=True)


class Parser(Protocol[T]):
    """A callable that converts raw retrieved data into records of type T.

    Receives the raw output of ``retrieve`` (an HTTP response, or a lazy
    iterable of responses for paginated sources) and the ``source`` instance,
    so a parser can read ``source.params`` or use ``source.session`` to fetch
    supplementary data while parsing.
    """

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> T: ...  # noqa: E704


class JsonParser(Parser[Any]):
    """Parse response as JSON, optionally drilling into a nested key path.

    With no arguments, returns the top-level parsed value::

        parse = parsers.JsonParser()          # response.json()

    With one or more keys, walks the parsed value before returning::

        parse = parsers.JsonParser("collections")     # response.json()["collections"]
        parse = parsers.JsonParser("data", "items")   # response.json()["data"]["items"]

    If the response is already a list at the top level, omit keys entirely.

    Pass ``shape`` (a ``TypedDict`` / ``list[...]`` / etc.) to validate the
    drilled-into value against the source's declared response shape. A mismatch
    logs the response and raises ``ResponseShapeError`` (the provider changed
    its API), instead of failing obscurely deeper in the pipeline::

        parse = parsers.JsonParser("collections", shape=list[CollectionRecord])
    """

    def __init__(self, *keys: str, shape: Any = None):
        self.keys = keys
        self.shape = shape

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> Any:
        data = response.json()
        for key in self.keys:
            data = data[key]
        if self.shape is not None:
            from waste_collection_schedule import response_shape

            data = response_shape.validate(
                data, self.shape, source_name=response_shape.source_name(source)
            )
        return data


class TextParser(Parser[str]):
    """Return response as plain text."""

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> str:
        return response.text


class HtmlParser(Parser[list[Tag]]):
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
        shape:    Optional list of CSS selectors that must each match at least
                  one element — the structural anchors the source depends on.
                  If one is missing (the provider redesigned the page), the
                  response is logged and ``ResponseShapeError`` is raised::

                      parse = parsers.HtmlParser("tr", skip=1, shape=["table.bins"])
    """

    def __init__(self, selector: str, skip: int = 0, shape: "list[str] | None" = None):
        self.selector = selector
        self.skip = skip
        self.shape = shape

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> list[Tag]:
        soup = BeautifulSoup(response.text, "html.parser")
        if self.shape:
            from waste_collection_schedule import response_shape

            name = response_shape.source_name(source)
            for sel in self.shape:
                response_shape.expect(
                    bool(soup.select(sel)),
                    source_name=name,
                    detail=f"required element {sel!r} not found",
                    raw=response.text,
                )
        return soup.select(self.selector)[self.skip :]


class IcsParser(Parser[list[tuple[datetime.date, str]]]):
    """Parse response as an iCalendar feed.

    Returns a list of (date, summary) tuples for all events in the next year.
    Use this with the default retriever and an ICSTransformer::

        parse = parsers.IcsParser()
        transformer = ICSTransformer(type_value_map={...})

    Pass ``shape`` (a minimum event count) to assert the feed parsed as expected;
    fewer events (e.g. the provider returned an HTML error page) logs the
    response and raises ``ResponseShapeError``.
    """

    def __init__(self, shape: "int | None" = None):
        self.shape = shape

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> list[tuple[datetime.date, str]]:
        from waste_collection_schedule.service.ICS import ICS

        events = ICS().convert(response.text)
        if self.shape is not None:
            from waste_collection_schedule import response_shape

            response_shape.expect(
                len(events) >= self.shape,
                source_name=response_shape.source_name(source),
                detail=f"expected at least {self.shape} ICS events, got {len(events)}",
                raw=response.text,
            )
        return events


class IcsEventsParser(Parser[list[IcsEvent]]):
    """Parse response as an iCalendar feed, exposing full event fields.

    Like :class:`IcsParser`, but returns ``IcsEvent(date, title, location,
    description)`` records instead of bare ``(date, summary)`` tuples. Use this
    with ``classify()`` when the source must inspect the ICS ``LOCATION`` or
    ``DESCRIPTION`` fields — for example to filter events by collection route::

        parse = parsers.IcsEventsParser()

        def classify(self, record) -> Collection | None:
            # record.title / record.location / record.description available
            return Collection(date=record.date, waste_type=...)

    Pass ``shape`` (a minimum event count) to assert the feed parsed as expected.
    """

    def __init__(self, shape: "int | None" = None):
        self.shape = shape

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> list[IcsEvent]:
        from waste_collection_schedule.service.ICS import ICS

        events = ICS().convert_events(response.text)
        if self.shape is not None:
            from waste_collection_schedule import response_shape

            response_shape.expect(
                len(events) >= self.shape,
                source_name=response_shape.source_name(source),
                detail=f"expected at least {self.shape} ICS events, got {len(events)}",
                raw=response.text,
            )
        return events
