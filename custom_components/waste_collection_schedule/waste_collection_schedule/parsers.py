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

from waste_collection_schedule import response_shape
from waste_collection_schedule.service.ICS import IcsEvent

if TYPE_CHECKING:
    import requests
    from curl_cffi import requests as _cffi_requests

    from waste_collection_schedule.base_source import BaseSource

    Response: TypeAlias = "requests.Response | _cffi_requests.Response"
else:
    Response = object

T = TypeVar("T", covariant=True)


def _expect_min_events(
    events: list, minimum: int | None, raw: str, source: Any
) -> None:
    """Shared shape check for the ICS parsers: at least ``minimum`` events.

    Fewer events (e.g. the provider returned an HTML error page) logs the
    response and raises ``ResponseShapeError``.
    """
    if minimum is None:
        return
    response_shape.expect(
        len(events) >= minimum,
        source_name=response_shape.source_name(source),
        detail=f"expected at least {minimum} ICS events, got {len(events)}",
        raw=raw,
    )


class Parser(Protocol[T]):
    """A callable that converts raw retrieved data into records of type T.

    Receives the raw output of ``retrieve`` (an HTTP response, or a lazy
    iterable of responses for paginated sources) and the ``source`` instance,
    so a parser can read ``source.params`` or use ``source.session`` to fetch
    supplementary data while parsing.
    """

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> T: ...


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
            data = response_shape.validate(
                data, self.shape, source_name=response_shape.source_name(source)
            )
        return data


class TextParser(Parser[str]):
    """Return response as plain text.

    Pass ``min_chars`` (a minimum character count) to flag an empty/error
    response (e.g. the provider returned a blank body or a short error page),
    which is logged and raises ``ResponseShapeError`` rather than parsing nothing.
    """

    def __init__(self, min_chars: "int | None" = None):
        self.min_chars = min_chars

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> str:
        text = response.text
        if self.min_chars is not None:
            response_shape.expect(
                len(text.strip()) >= self.min_chars,
                source_name=response_shape.source_name(source),
                detail=f"response text under {self.min_chars} chars (empty/error page?)",
                raw=text[:500],
            )
        return text


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
        require:  Optional list of CSS selectors that must each match at least
                  one element — the structural anchors the source depends on.
                  If one is missing (the provider redesigned the page), the
                  response is logged and ``ResponseShapeError`` is raised::

                      parse = parsers.HtmlParser("tr", skip=1, require=["table.bins"])
        from_json_key: When set, the HTML to parse is read from a field of a
                  JSON response instead of ``response.text`` — pass the key (or a
                  path of keys) holding the HTML string. This covers the common
                  pattern of an API returning rendered HTML inside JSON, e.g. the
                  OCAPI ``wasteservices`` endpoint many AU councils use::

                      parse = parsers.HtmlParser("article", from_json_key="responseContent")

                  ``response`` may also already be a plain ``dict``/``list``
                  (no ``.json()`` method) rather than an HTTP response object,
                  as returned by a retriever that pre-decodes JSON itself, e.g.
                  ``AchieveFormsRetriever`` -- the path is read straight off it::

                      parse = parsers.HtmlParser(
                          "tr", skip=1,
                          from_json_key=("integration", "transformed", "rows_data", "0", "UpcomingCollections"),
                      )
    """

    def __init__(
        self,
        selector: str,
        skip: int = 0,
        require: "list[str] | None" = None,
        from_json_key: "str | tuple[str, ...] | None" = None,
    ):
        self.selector = selector
        self.skip = skip
        self.require = require
        self.from_json_key = from_json_key

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> list[Tag]:
        if self.from_json_key is not None:
            # A retriever may already return decoded JSON (a dict/list) rather
            # than an HTTP response object (e.g. AchieveFormsRetriever, whose
            # runLookup call is itself a JSON POST/GET) -- use it directly in
            # that case instead of calling a nonexistent .json().
            data: Any = (
                response if isinstance(response, (dict, list)) else response.json()
            )
            keys = (
                (self.from_json_key,)
                if isinstance(self.from_json_key, str)
                else self.from_json_key
            )
            for key in keys:
                data = data[key]
            markup = str(data)
        else:
            markup = response.text
        soup = BeautifulSoup(markup, "html.parser")
        if self.require:
            name = response_shape.source_name(source)
            for sel in self.require:
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
        transform = ICSTransformer(type_value_map={...})

    Pass ``min_events`` (a minimum event count) to assert the feed parsed as
    expected; fewer events (e.g. the provider returned an HTML error page) logs
    the response and raises ``ResponseShapeError``.

    The remaining arguments are forwarded to ``service.ICS.ICS`` unchanged and
    shape how each VEVENT's summary becomes the ``(date, summary)`` tuple; see
    that class for the exact semantics:

    * ``offset`` — shift every date by this many days (a provider whose feed
      is dated one day off from the actual collection day).
    * ``regex`` — a pattern matched against the rendered title; when it
      matches, the title becomes the pattern's first capture group (trims a
      fixed prefix/suffix the provider adds around the bin name).
    * ``split_at`` — a pattern splitting one VEVENT's title into several
      entries on the same date (a combined round listed as one event, e.g.
      "Restmüll / Gelber Sack").
    * ``title_template`` — a Jinja2 template rendered with ``date`` bound to
      the ``icalevents`` event object (default ``"{{date.summary}}"``); use
      this to build the title from a field other than SUMMARY.

    All four default to ``ICS()``'s own defaults, so existing callers that
    only pass ``min_events`` are unaffected.
    """

    def __init__(
        self,
        min_events: "int | None" = None,
        offset: "int | None" = None,
        regex: "str | None" = None,
        split_at: "str | None" = None,
        title_template: str = "{{date.summary}}",
    ):
        self.min_events = min_events
        self.offset = offset
        self.regex = regex
        self.split_at = split_at
        self.title_template = title_template

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> list[tuple[datetime.date, str]]:
        from waste_collection_schedule.service.ICS import ICS

        events = ICS(
            offset=self.offset,
            regex=self.regex,
            split_at=self.split_at,
            title_template=self.title_template,
        ).convert(response.text)
        _expect_min_events(events, self.min_events, response.text, source)
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

    Pass ``min_events`` (a minimum event count) to assert the feed parsed as
    expected. ``offset``, ``regex``, ``split_at`` and ``title_template`` are
    forwarded to ``service.ICS.ICS`` exactly as in :class:`IcsParser`.
    """

    def __init__(
        self,
        min_events: "int | None" = None,
        offset: "int | None" = None,
        regex: "str | None" = None,
        split_at: "str | None" = None,
        title_template: str = "{{date.summary}}",
    ):
        self.min_events = min_events
        self.offset = offset
        self.regex = regex
        self.split_at = split_at
        self.title_template = title_template

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> list[IcsEvent]:
        from waste_collection_schedule.service.ICS import ICS

        events = ICS(
            offset=self.offset,
            regex=self.regex,
            split_at=self.split_at,
            title_template=self.title_template,
        ).convert_events(response.text)
        _expect_min_events(events, self.min_events, response.text, source)
        return events


class PdfTextParser(Parser[str]):
    """Extract the text layer of a PDF response (pypdf, no OCR).

    For providers whose calendar is a text-PDF (``pypdf`` text extraction
    returns the schedule). Returns the *whole page text as one string*. Because
    a text PDF is one blob that fans out into many rows, pair it with a custom
    ``preprocessor`` (defined as a method, not a bare function) that yields the
    rows; the default preprocessor / ``classify()`` expect per-record input and
    won't fit::

        parse = parsers.PdfTextParser(min_chars=200)
        transform = ICSTransformer(type_value_map={...})

        def preprocess(self, text, source=None):
            for date, key in _rows_from_text(text):   # source-specific parsing
                yield (date, key)

    Pass ``min_chars`` (a minimum character count) to flag an image-only/empty
    PDF, which is logged and raises ``ResponseShapeError`` rather than yielding
    nothing.
    """

    def __init__(self, min_chars: "int | None" = None):
        self.min_chars = min_chars

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> str:
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(response.content))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        if self.min_chars is not None:
            response_shape.expect(
                len(text.strip()) >= self.min_chars,
                source_name=response_shape.source_name(source),
                detail=f"PDF text under {self.min_chars} chars (image-only PDF?)",
                raw=text[:500],
            )
        return text


class XmlParser(Parser["list[Any]"]):
    """Parse XML and select elements by tag/XPath (lxml).

    Selects all elements matching ``path`` (an XPath or tag name), each passed
    to the transformer/classify. Omit ``path`` to get the root element back as a
    single-item list. Pass ``min_nodes`` (a minimum match count) to flag a
    changed feed::

        parse = parsers.XmlParser("collection")             # all <collection> nodes
        parse = parsers.XmlParser(".//event", min_nodes=1)   # XPath

    For a namespaced feed, pass ``namespaces`` (a prefix->URI map) and use the
    prefix in ``path`` instead of inlining ``{uri}tag``::

        parse = parsers.XmlParser(".//w:Collection", namespaces={"w": NS_URI})

    Note: ``min_nodes`` suits fixed feeds. For an address-lookup source where an
    unknown input legitimately returns zero nodes, leave ``min_nodes`` unset and
    rely on ``RAISE_ON_EMPTY`` instead, so a bad lookup is reported as a bad
    argument rather than a changed feed.
    """

    def __init__(
        self,
        path: "str | None" = None,
        min_nodes: "int | None" = None,
        namespaces: "dict[str, str] | None" = None,
    ):
        self.path = path
        self.min_nodes = min_nodes
        self.namespaces = namespaces

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> list:
        from lxml import etree  # type: ignore[attr-defined]

        root = etree.fromstring(response.content)
        elements = (
            root.findall(self.path, namespaces=self.namespaces) if self.path else [root]
        )
        if self.min_nodes is not None:
            response_shape.expect(
                len(elements) >= self.min_nodes,
                source_name=response_shape.source_name(source),
                detail=f"expected at least {self.min_nodes} XML nodes, got {len(elements)}",
                raw=response.text,
            )
        return elements


class CsvParser(Parser["list[dict[str, str]]"]):
    """Parse CSV into a list of dict rows (csv.DictReader).

    Each row is a ``{column: value}`` dict, so it pairs with ``JsonTransformer``
    (``date_key`` / ``type_key`` are column names). Pass ``require`` (a list of
    required column names) to flag a changed export whose header no longer has
    the columns the source reads::

        parse = parsers.CsvParser(require=["date", "type"])
    """

    def __init__(self, delimiter: str = ",", require: "list[str] | None" = None):
        self.delimiter = delimiter
        self.require = require

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[dict[str, str]]":
        import csv
        import io

        # Decode utf-8-sig so a UTF-8 BOM doesn't contaminate the first column
        # name (a common export quirk).
        text = response.content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text), delimiter=self.delimiter)
        rows = list(reader)
        if self.require:
            columns = set(reader.fieldnames or [])
            missing = [c for c in self.require if c not in columns]
            response_shape.expect(
                not missing,
                source_name=response_shape.source_name(source),
                detail=f"CSV missing expected columns: {missing}",
                raw=response.text[:500],
            )
        return rows
