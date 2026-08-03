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
import logging
import re
from collections.abc import Callable, Iterable, Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    Protocol,
    TypeVar,
    cast,
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

_LOGGER = logging.getLogger(__name__)

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

    Args:
        parser: the inner parser, applied to each response.
        skip_failures: keep going when one response does not parse, instead of
            failing the whole fetch. For a provider publishing one file per
            year, where next year's file is empty or absent for a while after
            the turnover and the current year's is perfectly good. Off by
            default, because a response that will not parse is normally the
            provider changing shape, which should be heard about rather than
            silently half-swallowed.
    """

    def __init__(self, parser: Parser, *, skip_failures: bool = False):
        self.parser = parser
        self.skip_failures = skip_failures

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[Any]":
        responses = [response] if hasattr(response, "status_code") else response  # type: ignore[list-item]
        records: list[Any] = []
        for item in responses:  # type: ignore[union-attr]
            try:
                records.extend(self.parser(item, source))
            except Exception as error:
                if not self.skip_failures:
                    raise
                _LOGGER.debug(
                    "EachResponse: skipping a response that failed: %s", error
                )
        return records


class FirstNonEmptyBranch(Parser["list[Any]"]):
    """Parse a fallback retriever's branches, keeping the first that has records.

    The consumer half of
    :class:`~waste_collection_schedule.retrievers.FallbackRetriever`. Where
    :class:`EachResponse` maps one parser over every response and concatenates
    the lot, this maps a *different* parser over each branch — the branches are
    alternative feeds for the same schedule, not parts of one — and stops at the
    first that yielded anything::

        retrieve = retrievers.FallbackRetriever(
            retrievers.Branch("ics", retrievers.follow_link(r"\\.ics$")),
            retrievers.Branch("page", retrievers.reuse_prepared),
            prepare=_collection_page,
        )
        parse = parsers.FirstNonEmptyBranch(
            {"ics": parsers.IcsParser(), "page": parsers.HtmlLabelledDates(...)}
        )

    Branches are pulled one at a time, so the second feed is only requested when
    the first produced nothing — which is the point of having a fallback rather
    than fetching both.

    A branch has not worked out when its fetch raised, when its parser raised,
    or when it parsed to no records: the three ways a provider says "not here"
    (an outage, an error page where a calendar was expected, and a 200 carrying
    nothing). Earlier failures are logged and dropped. The last branch attempted
    has the last word, so its error surfaces to the user, and its empty result
    reaches ``RAISE_ON_EMPTY``, rather than the user being told about a feed
    they did not configure.

    Args:
        branches: ``{branch label: parser}``. The order tried is the
            retriever's, not this mapping's. A branch whose label is missing
            here is a configuration error and raises.
    """

    def __init__(self, branches: "Mapping[Any, Parser]"):
        self.branches = dict(branches)

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[Any]":
        records: list[Any] = []
        error: Exception | None = None
        attempted = False
        for attempt in cast("Iterable[Any]", response):
            attempted = True
            records, error = [], attempt.error
            if error is None:
                if attempt.label not in self.branches:
                    raise ValueError(
                        f"FirstNonEmptyBranch has no parser for branch "
                        f"{attempt.label!r} (known: {sorted(map(str, self.branches))})"
                    )
                try:
                    records = list(self.branches[attempt.label](attempt.raw, source))
                except Exception as failure:
                    error = failure
            if records:
                return records
            _LOGGER.debug(
                "FirstNonEmptyBranch: branch %r yielded nothing (%s)",
                attempt.label,
                error or "no records",
            )
        if not attempted:
            raise ValueError("FirstNonEmptyBranch: no branch was applicable")
        if error is not None:
            raise error
        return records


class LabelledSections(Parser["list[tuple[Any, Any]]"]):
    """Split a JSON object into ``(label, section)`` records, one per named field.

    For an API that answers with one object per collection round, keyed by field
    name, rather than with a list of events::

        {"trash": {...}, "recycling": {...}, "bulkyWaste": {...}}

    Each named field becomes one record carrying the round's label and that
    round's whole object. That is the same ``(label, payload)`` shape
    :class:`~waste_collection_schedule.service.ArcGis.ArcGisMultiFeatureParser`
    produces for a layer per round, so one preprocessor and one transformer read
    both. Reach for it when the round's dates sit inside a nested structure a
    flat parser cannot express, and pair it with
    :class:`~waste_collection_schedule.preprocessors.RecurrenceExpander`, whose
    ``describe`` callable is where reading a base date and cadence out of a
    provider's own layout belongs. When each field simply holds an array of
    dates, :class:`KeyedDateListsParser` is the simpler fit.

    Records come out in ``sections`` order. A field the payload omits, or whose
    value is null, contributes nothing, and a payload that is not an object at
    all yields no records rather than raising, so a fallback branch can take
    over.

    Args:
        sections: ``{json field: label}``, or an iterable of field names used as
            their own labels.
        keys: optional path drilled into before the sections are read, exactly
            as :class:`JsonParser` does.
        argument: the ``source.params`` field the payload was fetched by, blamed
            when none of the sections were present. An index keyed by a
            user-supplied id that came back with nothing in it is a wrong id,
            not an empty schedule, and saying so names the field the HA UI
            should highlight. This is the same pair
            :class:`~waste_collection_schedule.service.ArcGis.ArcGisMultiFeatureParser`
            takes, and it composes with
            :class:`FirstNonEmptyBranch` the same way: the raise only reaches
            the user if this was the last branch tried, so an earlier feed
            still falls through to a later one. Leave unset to return no
            records instead.
        hint: guidance shown with that error.
    """

    def __init__(
        self,
        sections: "Mapping[str, Any] | Iterable[str]",
        *keys: str,
        argument: "str | None" = None,
        hint: str = "",
    ):
        self.sections: dict[str, Any] = (
            dict(sections)
            if isinstance(sections, Mapping)
            else {name: name for name in sections}
        )
        self.keys = keys
        self.argument = argument
        self.hint = hint

    def _blame(self, source: "BaseSource | None") -> None:
        argument = str(self.argument)
        value = source.params.get(argument) if source is not None else None
        raise SourceArgumentNotFound(argument, value, self.hint)

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[tuple[Any, Any]]":
        response.raise_for_status()
        data = response.json()
        try:
            for key in self.keys:
                data = data[key]
        except (KeyError, IndexError, TypeError):
            data = None
        if not isinstance(data, dict):
            if self.argument is not None:
                self._blame(source)
            return []
        records = [
            (label, data[field])
            for field, label in self.sections.items()
            if data.get(field) is not None
        ]
        if not records and self.argument is not None:
            self._blame(source)
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


class KeyedDateListsParser(Parser["list[tuple[Any, str]]"]):
    """Parse a payload holding one array of dates per round, keyed by field name.

    The multi-round sibling of :class:`DateListParser`. Instead of one flat
    array for a single-stream provider, the payload carries a field per round,
    each holding that round's dates and nothing else to say which round it is::

        [{"allBinDays": ["01-07-2026", ...], "allRecycleDays": [...], ...}]

    ``keys`` drills to the object holding those fields exactly as
    :class:`JsonParser` does, except that an index into a list is written as an
    int. Each listed field's dates are then paired with the field's own name, so
    the round's name stays in the transformer's ``type_value_map`` where every
    other source declares it, rather than being hardcoded in a ``classify()``::

        parse = parsers.KeyedDateListsParser(0, fields=_TYPE_MAP)
        transform = RowTransformer(
            parse_date=date_parsers.for_format("%d-%m-%Y"),
            type_value_map=_TYPE_MAP,
        )

    Rows come out grouped by field, in ``fields`` order. A field the payload
    omits contributes nothing, and a key path that does not resolve (the
    provider answered a bad lookup with an empty list) yields no rows at all, so
    pair this with ``RAISE_ON_EMPTY`` on an address/lookup source.

    Args:
        keys: optional path to the object carrying the arrays.
        fields: the field names to read, one per round. Pass the transformer's
            ``type_value_map`` directly; its keys are exactly that set.
    """

    def __init__(self, *keys: "str | int", fields: Iterable[str]):
        self.keys = keys
        self.fields = tuple(fields)

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[tuple[Any, str]]":
        data = response.json()
        try:
            for key in self.keys:
                data = data[key]
        except (KeyError, IndexError, TypeError):
            return []
        if not isinstance(data, dict):
            return []
        return [
            (value, field) for field in self.fields for value in (data.get(field) or [])
        ]


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


class HtmlLabelledDates(Parser["list[tuple[str, str]]"]):
    """One ``(date, label)`` row per block of a card-style collection page.

    For the "your next collections" preview a council renders as a row of cards
    rather than as a table: each block carries its own round name and its own
    date, so there is no column structure for :class:`HtmlParser` plus
    ``HtmlTransformer`` to walk, and no single element holding the date for
    :class:`HtmlTextParser`. This selects each block, reads the two halves out
    of it, and yields the ordinary ``(date, label)`` row the shared row
    transformers already consume::

        parse = parsers.HtmlLabelledDates(
            "div.collection-details",
            label="span.legend-wrapper",
            date_after="Next Collection",
            date_pattern=r"(\\d{1,2}-\\w{3}-\\d{4})",
        )
        transform = RowTransformer(
            parse_date=date_parsers.for_format("%d-%b-%Y"), type_value_map={...}
        )

    A block missing either half is skipped rather than failing the fetch: a
    provider that renders a blank placeholder card should not take the whole
    schedule down with it (see #6860).

    Args:
        block: CSS selector for each collection block.
        label: CSS selector, within the block, for the round's name.
        date: CSS selector, within the block, for the element holding the date.
        date_after: alternative to ``date`` for a page that captions the date
            instead of classing it: the caption's exact text, whose next
            sibling element holds the date. Blocks commonly caption several
            fields ("Frequency", "Next Collection") with the same class, which
            is exactly when a selector cannot tell them apart.
        date_pattern: regex searched in the date text; group 1 (or the whole
            match, when the pattern has no group) is the date. Use it to drop
            the weekday a provider prefixes ("Fri, 17-Jul-2026"). Text that does
            not match is skipped.
        parse_date: optional ``callable(str) -> datetime.date`` (see
            :mod:`~waste_collection_schedule.date_parsers`) turning the matched
            text into a real date here, rather than leaving that to a
            ``RowTransformer(parse_date=...)`` downstream. Set it when this
            parser is one branch of a
            :class:`FirstNonEmptyBranch` whose other branch already yields
            dates: the branches must agree on their record shape, because one
            transformer reads them both. Text the callable rejects is skipped,
            on the same reasoning as a block missing a half.
    """

    def __init__(
        self,
        block: str,
        *,
        label: str,
        date: "str | None" = None,
        date_after: "str | None" = None,
        date_pattern: "str | None" = None,
        parse_date: "Callable[[str], datetime.date] | None" = None,
    ):
        if (date is None) == (date_after is None):
            raise ValueError("HtmlLabelledDates needs exactly one of date/date_after")
        self.block = block
        self.label = label
        self.date = date
        self.date_after = date_after
        self.date_pattern = re.compile(date_pattern) if date_pattern else None
        self.parse_date = parse_date

    def _date_text(self, element: Tag) -> "str | None":
        if self.date is not None:
            found = element.select_one(self.date)
            return found.get_text(strip=True) if found is not None else None
        caption = element.find(string=self.date_after)
        holder = caption.parent if caption is not None else None
        sibling = holder.find_next_sibling() if isinstance(holder, Tag) else None
        return sibling.get_text(strip=True) if isinstance(sibling, Tag) else None

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[tuple[Any, str]]":
        soup = BeautifulSoup(response.text, "html.parser")
        rows: list[tuple[Any, str]] = []
        for element in soup.select(self.block):
            named = element.select_one(self.label)
            name = named.get_text(strip=True) if named is not None else ""
            text = self._date_text(element) if name else None
            if not name or not text:
                continue
            if self.date_pattern is not None:
                match = self.date_pattern.search(text)
                if match is None:
                    continue
                text = match.group(1) if match.groups() else match.group(0)
            if self.parse_date is None:
                rows.append((text, name))
                continue
            try:
                rows.append((self.parse_date(text), name))
            except (ValueError, TypeError):
                continue
        return rows


class HtmlMonthRows(Parser["list[tuple[datetime.date, str]]"]):
    """A table with a month per row and a collection round per column.

    The HTML sibling of
    :class:`~waste_collection_schedule.preprocessors.PdfMonthColumns`. A council
    that publishes its year as one table puts the month in the first column and
    gives each round a column of its own, whose cell lists the days it is
    collected that month::

        | Miesiąc      | Zmieszane  | Papier | Bio      |
        | lipiec 2026  | 3, 17, 31  | 10     | 7, 14, 21|

    Each day number becomes one ``(date, round name)`` row, the round's name
    taken from its column header::

        parse = parsers.HtmlMonthRows(require=("miesiąc", "papier"))
        transform = ICSTransformer(type_value_map=TYPE_MAP)

    The month cell is read with :func:`recurrence.month`, so a month named in
    any supported language resolves, including the inflected forms a date reads
    in. A month cell that names no month is skipped, which is what drops a
    totals or footnote row without having to describe it.

    Args:
        require: header texts (lowercased, matched exactly) that the wanted
            table must all carry. A page usually holds several tables, and the
            schedule is the one whose headers name the rounds. Unset takes the
            first table on the page.
        month_column: index of the month column (default 0). The columns after
            it are the rounds, in order.
        header_row: which row of the ``<thead>`` carries the round names
            (default -1, the last). A two-row header, grouping columns above
            and naming them below, is common.
        separator: regex the day list in a cell is split on (default a comma).
        year: fallback when the month cell names no year (default the current
            year at fetch time).
    """

    def __init__(
        self,
        *,
        require: "Iterable[str] | None" = None,
        month_column: int = 0,
        header_row: int = -1,
        separator: str = ",",
        year: "int | None" = None,
    ):
        self.require = frozenset(require) if require is not None else None
        self.month_column = month_column
        self.header_row = header_row
        self.separator = re.compile(separator)
        self.year = year

    def _table(self, soup: BeautifulSoup) -> "Tag | None":
        for candidate in soup.find_all("table"):
            if self.require is None:
                return candidate
            headers = {
                th.get_text(strip=True).lower() for th in candidate.find_all("th")
            }
            if self.require <= headers:
                return candidate
        return None

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        from waste_collection_schedule import recurrence

        soup = BeautifulSoup(response.text, "html.parser")
        table = self._table(soup)
        if table is None:
            return []

        head = table.find("thead")
        body = table.find("tbody")
        if not isinstance(head, Tag) or not isinstance(body, Tag):
            return []

        header_rows = head.find_all("tr")
        if not header_rows:
            return []
        cells = header_rows[self.header_row].find_all(["th", "td"])
        rounds = [c.get_text(strip=True) for c in cells[self.month_column + 1 :]]

        default_year = self.year or datetime.date.today().year
        rows: list[tuple[datetime.date, str]] = []
        for row in body.find_all("tr"):
            values = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(values) < 2:
                continue

            parts = values[self.month_column].split()
            if not parts:
                continue
            month = recurrence.month(parts[0])
            if month is None:
                continue
            year = (
                int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else default_year
            )

            for index, name in enumerate(rounds):
                column = self.month_column + 1 + index
                if column >= len(values):
                    continue
                for day in self.separator.split(values[column].replace(" ", "")):
                    if not day.isdigit():
                        continue
                    try:
                        rows.append((datetime.date(year, month, int(day)), name))
                    except ValueError:
                        continue
        return rows


class HtmlTextParser(Parser[str]):
    """Parse response as HTML and return its visible text.

    For the page that states its schedule in prose rather than in a table: "if
    your regular pick-up is Monday & Thursday (District 1) ...", or a run of
    dates listed under a heading. There is no row to select and no attribute to
    read, so :class:`HtmlParser` has nothing to hand a transformer; what the
    source wants is the sentence. This strips the markup and hands over the text,
    which the text-shaped preprocessors then read::

        parse = parsers.HtmlTextParser()
        preprocess = preprocessors.TextGroupedDates(keys=TYPE_MAP, ...)

    It is the HTML sibling of :class:`PdfTextParser`, and produces the same
    thing: one string for the whole document. Pair it with a preprocessor that
    fans that string out into records (:class:`~waste_collection_schedule.preprocessors.TextGroupedDates`,
    :class:`~waste_collection_schedule.preprocessors.TextCalendarGrid`, or an
    :class:`~waste_collection_schedule.preprocessors.ArgumentLookup` reading a
    table out of the prose); the default preprocessor and ``classify()`` both
    expect per-record input and won't fit.

    Args:
        separator: placed between the text of adjacent elements, so words either
            side of a tag boundary do not run together. Default a single space;
            pass ``"\\n"`` to keep the page's block structure.
        collapse_whitespace: fold every run of whitespace (including the newlines
            and indentation of the source markup) to one space, so a pattern can
            be written against the sentence as it reads rather than against the
            HTML's line breaks. On by default.
        min_chars: minimum character count expected. Fewer (the provider returned
            an empty body or a short error page) logs the response and raises
            ``ResponseShapeError`` rather than parsing nothing.
    """

    def __init__(
        self,
        *,
        separator: str = " ",
        collapse_whitespace: bool = True,
        min_chars: "int | None" = None,
    ):
        self.separator = separator
        self.collapse_whitespace = collapse_whitespace
        self.min_chars = min_chars

    def __call__(self, response: Response, source: "BaseSource | None" = None) -> str:
        text = BeautifulSoup(response.text, "html.parser").get_text(self.separator)
        if self.collapse_whitespace:
            text = re.sub(r"\s+", " ", text)
        if self.min_chars is not None:
            response_shape.expect(
                len(text.strip()) >= self.min_chars,
                source_name=response_shape.source_name(source),
                detail=f"page text under {self.min_chars} chars (empty/error page?)",
                raw=response.text[:500],
            )
        return text


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

    Set ``concatenated`` for a provider that glues several VCALENDAR blocks into
    one response (an observed quirk: the calendar library reads only the first,
    silently losing the rest). Each block is then converted separately and
    duplicate ``(date, summary)`` events are dropped, since a provider stitching
    calendars together tends to repeat events across the seam.
    """

    def __init__(
        self,
        min_events: "int | None" = None,
        offset: "int | None" = None,
        regex: "str | None" = None,
        split_at: "str | None" = None,
        title_template: str = "{{date.summary}}",
        concatenated: bool = False,
    ):
        self.min_events = min_events
        self.offset = offset
        self.regex = regex
        self.split_at = split_at
        self.title_template = title_template
        self.concatenated = concatenated

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> list[tuple[datetime.date, str]]:
        from waste_collection_schedule.service.ICS import ICS

        ics = ICS(
            offset=self.offset,
            regex=self.regex,
            split_at=self.split_at,
            title_template=self.title_template,
        )
        text = response.text
        if self.concatenated and text.count("BEGIN:VCALENDAR") > 1:
            events = []
            seen: set = set()
            for block in text.split("BEGIN:VCALENDAR")[1:]:
                for event in ics.convert("BEGIN:VCALENDAR" + block):
                    if event in seen:
                        continue
                    seen.add(event)
                    events.append(event)
        else:
            events = ics.convert(text)
        _expect_min_events(events, self.min_events, text, source)
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
