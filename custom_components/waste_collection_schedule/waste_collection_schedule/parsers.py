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
    parse = parsers.DateListParser("cal", label="Blaue Tonne")  # flat date array
"""

import datetime
from collections.abc import Callable, Iterable
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    Protocol,
    TypeVar,
)

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import IcsEvent

if TYPE_CHECKING:
    import requests
    from curl_cffi import requests as _cffi_requests

    from waste_collection_schedule.base_source import BaseSource

    type Response = "requests.Response | _cffi_requests.Response"
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


class EachResponse(Parser["list[Any]"]):
    """Apply an inner parser to every response of a multi-response retrieve.

    ``retrieve`` may hand back an iterable of responses rather than one: a
    provider that publishes a separate calendar file per year (see
    :class:`~waste_collection_schedule.retrievers.YearlyRetriever`), or a
    paginated API. Each response parses exactly as a single one would, so this
    maps the inner parser over them and concatenates the records, leaving the
    rest of the pipeline seeing one flat list and the source needing no
    ``parse`` of its own::

        retrieve = retrievers.YearlyRetriever(fetch=_calendar_for_year)
        parse = parsers.EachResponse(parsers.IcsParser())

    A single response is passed straight through to the inner parser, so a
    retriever that returns one response in some configurations and several in
    others needs no special casing. Records are concatenated in the order the
    retriever produced the responses.

    Note that a per-response shape check (an ``IcsParser(min_events=...)``, say)
    then applies to *each* response individually, which is usually what you
    want: a year that came back empty is caught rather than masked by a healthy
    neighbouring year.
    """

    def __init__(self, parser: Parser):
        self.parser = parser

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[Any]":
        responses = [response] if hasattr(response, "status_code") else response  # type: ignore[list-item]
        records: list[Any] = []
        for item in responses:  # type: ignore[union-attr]
            records.extend(self.parser(item, source))
        return records


class ArgumentGuard(Parser[Any]):
    """Reject a response that is not the expected feed, blaming the argument.

    Plenty of providers answer an unknown lookup key with HTTP 200 and an
    ordinary web page rather than an error. The pipeline then parses nothing and
    the user is told they have no collections, when in truth their town or street
    was misspelt. This wraps the real parser in the cheap marker check that tells
    the two apart, and raises the argument error the HA UI knows how to present,
    listing the valid values when the source can find them::

        parse = parsers.ArgumentGuard(
            parsers.IcsEventsParser(min_events=1),
            argument="city",
            contains="BEGIN:VCALENDAR",
            suggestions=_possible_cities,
            hint="spell the city exactly as in the links on the web-app page",
        )

    Args:
        parser: the inner parser, applied once the response passes the check.
        argument: the config param blamed for the mismatch.
        contains: text that every valid response carries.
        suggestions: optional ``callable(source) -> Iterable[str]`` returning the
            valid values, usually read off the provider's own index page. It runs
            only on the failure path, so a healthy fetch pays nothing for it. If
            it fails in turn, the plainer ``hint`` error is raised instead, so a
            second outage cannot hide the first error.
        hint: guidance shown when no suggestions are available.
    """

    def __init__(
        self,
        parser: Parser,
        *,
        argument: str,
        contains: str,
        suggestions: "Callable[[BaseSource | None], Iterable[str]] | None" = None,
        hint: str = "",
    ):
        self.parser = parser
        self.argument = argument
        self.contains = contains
        self.suggestions = suggestions
        self.hint = hint

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> Any:
        if self.contains not in response.text:
            self._reject(source)
        return self.parser(response, source)

    def _reject(self, source: "BaseSource | None") -> None:
        value = source.params.get(self.argument) if source is not None else None
        if self.suggestions is not None:
            try:
                options = list(self.suggestions(source))
            except Exception as e:
                raise SourceArgumentNotFound(self.argument, value, self.hint) from e
            raise SourceArgumentNotFoundWithSuggestions(self.argument, value, options)
        raise SourceArgumentNotFound(self.argument, value, self.hint)


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


class DateListParser(Parser["list[tuple[str, str]]"]):
    """Parse a JSON payload that is a flat array of date strings.

    For a single-stream provider: the response carries dates only, with no waste
    type field, because the whole feed is one collection round (e.g. a "blue
    bin" only service)::

        {"cal": ["2026-01-13", "2026-02-10", ...]}

    ``keys`` drills into the payload exactly as :class:`JsonParser` does, then
    each remaining date is paired with the fixed ``label`` so the shared
    :class:`~waste_collection_schedule.transformers.RowTransformer` can map that
    label to a canonical WasteType. That keeps the round's name in the source's
    ``type_value_map`` where every other source declares it, instead of hiding a
    hardcoded WasteType inside a ``classify()``::

        parse = parsers.DateListParser("cal", label="Blaue Tonne")
        transform = RowTransformer(type_value_map={"Blaue Tonne": RECYCLABLES})

    Args:
        keys: Optional key path to the array (omit if the payload is the array).
        label: The round's raw label, attached to every date. The transformer
            maps it, so use the provider's own wording.
        drop_values: Placeholder entries to discard before pairing. A fixed-size
            array padded with a filler date is common in PHP-backed feeds, which
            spell "no date" as the SQL zero date ``"0000-00-00"``; without this
            the filler reaches the transformer and fails to parse::

                parse = parsers.DateListParser(
                    "cal", label="Blaue Tonne", drop_values=("0000-00-00",)
                )
    """

    def __init__(
        self,
        *keys: str,
        label: str,
        drop_values: Iterable[str] = (),
    ):
        self.keys = keys
        self.label = label
        self.drop_values = frozenset(drop_values)

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[tuple[str, str]]":
        data = response.json()
        for key in self.keys:
            data = data[key]
        return [(value, self.label) for value in data if value not in self.drop_values]


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


class AttributeJsonParser(Parser["list[Any]"]):
    """Parse a JSON payload carried in an HTML element's attribute.

    The mirror image of ``HtmlParser(from_json_key=...)``: rather than HTML
    rendered inside a JSON field, this is a JSON document embedded in a ``data-``
    attribute of a server-rendered page. Swiss municipal sites on the "i-web" CMS
    ship a whole collection table that way, and the same trick is common wherever
    a table widget is hydrated client-side::

        parse = parsers.AttributeJsonParser(
            "[data-entities]", "data-entities", "data",
            require_keys=("_anlassDate",),
            strip_html=True,
        )

    Args:
        selector: CSS selector for the elements carrying the attribute.
        attribute: the attribute holding the JSON. BeautifulSoup has already
            HTML-unescaped the value, so it is decoded as it stands.
        keys: optional key path into the decoded JSON, walked exactly as
            :class:`JsonParser` walks one.
        require_keys: field names a record must carry for its block to be the
            one wanted. A page routinely holds several such payloads (a legend
            as well as the schedule), and the first block with a record carrying
            all of these wins. A block that is not JSON, or whose key path does
            not resolve, is skipped.
        strip_html: reduce every string field of every record to its visible
            text. These payloads commonly hold an HTML fragment per field (an
            ``<a>`` around the name, a pair of responsive ``<span>``s around the
            date), which no transformer should have to unpick.

    Returns an empty list when no block matches, so pair it with
    ``RAISE_ON_EMPTY`` on an address/lookup source.
    """

    def __init__(
        self,
        selector: str,
        attribute: str,
        *keys: str,
        require_keys: Iterable[str] = (),
        strip_html: bool = False,
    ):
        self.selector = selector
        self.attribute = attribute
        self.keys = keys
        self.require_keys = tuple(require_keys)
        self.strip_html = strip_html

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[Any]":
        import json

        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup.select(self.selector):
            blob = element.get(self.attribute)
            if not isinstance(blob, str):
                continue
            try:
                data = json.loads(blob)
                for key in self.keys:
                    data = data[key]
            except (ValueError, TypeError, KeyError, IndexError):
                continue
            records = list(data or [])
            if self.require_keys and not any(
                isinstance(record, dict)
                and all(key in record for key in self.require_keys)
                for record in records
            ):
                continue
            if self.strip_html:
                return [_visible_text_values(record) for record in records]
            return records
        return []


def _visible_text_values(record: Any) -> Any:
    """Reduce a record's HTML-fragment string values to whitespace-collapsed text."""
    if not isinstance(record, dict):
        return record
    return {
        key: (
            BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
            if isinstance(value, str)
            else value
        )
        for key, value in record.items()
    }


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
    description)`` records instead of bare ``(date, summary)`` tuples. Reach for
    it when the ICS ``LOCATION``/``DESCRIPTION`` matter.

    To simply *preserve* LOCATION and DESCRIPTION on the calendar event, pair it
    with the standard :class:`~waste_collection_schedule.transformers.ICSTransformer`;
    it carries both through automatically, no extra config::

        parse = parsers.IcsEventsParser()
        transform = ICSTransformer(type_value_map={...})

    Use ``classify()`` instead when the source must *inspect* those fields — for
    example to filter events by collection route::

        parse = parsers.IcsEventsParser()

        def classify(self, record) -> Collection | None:
            # record.title / record.location / record.description available
            return Collection(date=record.date, waste_type=...)

    (Plain :class:`IcsParser` remains the default when metadata is not needed:
    it yields lighter ``(date, summary)`` tuples.)

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
    a text PDF is one blob that fans out into many rows, pair it with a
    preprocessor that yields those rows; the default preprocessor and
    ``classify()`` both expect per-record input and won't fit. Where the text
    groups its dates under a round's label,
    :class:`~waste_collection_schedule.preprocessors.TextGroupedDates` does the
    whole job declaratively::

        parse = parsers.PdfTextParser(min_chars=200)
        preprocess = preprocessors.TextGroupedDates(
            keys=TYPE_MAP,
            date_pattern=r"\\b(?P<month>\\d{2})\\.(?P<day>\\d{2})\\.",
            year_pattern=r"(\\d{4})\\.\\s*évi",
        )
        transform = ICSTransformer(type_value_map=TYPE_MAP)

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


class PdfWord(NamedTuple):
    """A run of text on a PDF page with its horizontal span (PDF points)."""

    text: str
    x0: float
    x1: float


class PdfRow(NamedTuple):
    """One horizontal line of a PDF table: its page, vertical position and words.

    ``y`` is the pdfminer baseline (larger = higher up the page). ``words`` are
    the runs of text sharing this line, sorted left-to-right by ``x0``.
    """

    page: int
    y: float
    words: tuple[PdfWord, ...]


class PdfTableParser(Parser["list[PdfRow]"]):
    """Extract positioned text from a text PDF, grouped into rows (pdfminer.six).

    For a text PDF laid out as a table or grid whose columns plain
    ``extract_text`` collapses (e.g. a calendar showing several months
    side-by-side). Rather than guess column boundaries from character offsets,
    this reads each text run's real coordinates and clusters runs sharing a
    horizontal line into a :class:`PdfRow`. The preprocessor then bins each
    row's words into columns by ``x0``; for the usual printed month-grid
    calendar,
    :class:`~waste_collection_schedule.preprocessors.PdfCalendarColumns` does
    that from three geometry numbers, leaving the source to say only what the
    printing means::

        parse = parsers.PdfTableParser(min_words=50)
        preprocess = preprocessors.PdfCalendarColumns(
            column_bounds=(300.0,),
            day_bands={0: (30.0, 66.0), 1: (340.0, 375.0)},
            header_y=845.0,
        )

    No OCR. Pass ``min_words`` (a minimum total run count) to flag an
    image-only/empty PDF, which is logged and raises ``ResponseShapeError``
    rather than yielding nothing.

    Args:
        y_tolerance: runs whose baselines differ by at most this many points
            are treated as the same row (default 3.0).
        min_words: minimum total text runs expected across the document.
    """

    def __init__(self, *, y_tolerance: float = 3.0, min_words: "int | None" = None):
        self.y_tolerance = y_tolerance
        self.min_words = min_words

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[PdfRow]":
        from io import BytesIO

        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LAParams, LTTextContainer, LTTextLineHorizontal

        # (page, y1, x0, x1, text) for every text run on every page.
        runs: list[tuple[int, float, float, float, str]] = []
        for page_no, layout in enumerate(
            extract_pages(BytesIO(response.content), laparams=LAParams())
        ):
            for element in layout:
                if not isinstance(element, LTTextContainer):
                    continue
                for line in element:
                    if not isinstance(line, LTTextLineHorizontal):
                        continue
                    text = line.get_text().strip()
                    if text:
                        runs.append((page_no, line.y1, line.x0, line.x1, text))

        if self.min_words is not None:
            response_shape.expect(
                len(runs) >= self.min_words,
                source_name=response_shape.source_name(source),
                detail=(
                    f"PDF yielded {len(runs)} text runs, under {self.min_words} "
                    "(image-only PDF?)"
                ),
                raw=" ".join(r[4] for r in runs)[:500],
            )

        # Cluster runs into rows: same page, baselines within y_tolerance.
        rows: list[PdfRow] = []
        current: list[tuple[int, float, float, float, str]] = []

        def flush() -> None:
            if not current:
                return
            page = current[0][0]
            y = current[0][1]
            words = tuple(
                PdfWord(text, x0, x1)
                for _, _, x0, x1, text in sorted(current, key=lambda r: r[2])
            )
            rows.append(PdfRow(page=page, y=y, words=words))

        # Top-to-bottom, then left-to-right within a page.
        for run in sorted(runs, key=lambda r: (r[0], -r[1], r[2])):
            if (
                current
                and run[0] == current[0][0]
                and abs(run[1] - current[0][1]) <= self.y_tolerance
            ):
                current.append(run)
            else:
                flush()
                current = [run]
        flush()
        return rows


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
