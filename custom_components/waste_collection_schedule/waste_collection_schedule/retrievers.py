"""Standard retrieval methods for waste collection sources.

Each retriever is a typed callable that takes a source instance and returns a
raw HTTP response. A retriever is configured either declaratively (passing the
URL/params/headers to its constructor, optionally as callables resolved against
``source.params``) or implicitly via the zero-config default instances, which
read ``API_URL`` / ``_params`` / ``_headers`` etc. from the source.

Every curl_cffi retriever issues its request through the single shared
``source.session`` (created once per source, browser-impersonating), so the
connection, cookies and TLS handshake are reused across the retrieve step and
any follow-up requests a parser makes. Retrievers never construct their own
session. A retriever only does HTTP: it must not inspect or parse the response
body (that is the parser's job), which keeps retrieve and parse orthogonal.

Preferred retrievers (curl_cffi, browser impersonation — works on
Cloudflare-protected sites and regular sites alike):

    retrieve = retrievers.http_get    # zero-config GET — default in BaseSource
    retrieve = retrievers.http_post   # zero-config POST

    # or configured explicitly:
    retrieve = retrievers.HttpGetRetriever(url="https://example.com/api")
    retrieve = retrievers.HttpGetRetriever(url=lambda uprn: f".../{uprn}")

Explicit fallback (plain requests — only use if curl_cffi causes a specific
problem):

    retrieve = retrievers.LegacyHttpGetRetriever(url=...)
    retrieve = retrievers.LegacyHttpPostRetriever(url=...)
    retrieve = retrievers.LegacySslHttpGetRetriever(url=...)
"""

from __future__ import annotations

import datetime
import json
import logging
import re
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple, Protocol, TypeVar, cast
from urllib.parse import urljoin
from weakref import WeakKeyDictionary

import requests as _plain_requests
from bs4 import BeautifulSoup, Tag

if TYPE_CHECKING:
    from curl_cffi import requests as _cffi_requests

    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

type Response = "_plain_requests.Response | _cffi_requests.Response"

type HeadersType = Mapping[str, str | None] | None
type ParamsType = dict | list | tuple | None
type JsonType = dict | list | None

type SourceParams = dict[str, Any]
type UrlArgs = Callable[..., str] | str
type ParamsArgs = Callable[..., ParamsType] | ParamsType
type HeadersArgs = Callable[..., HeadersType] | HeadersType
type AnyArgs = Callable[..., Any] | Any
type JsonArgs = Callable[..., JsonType] | JsonType


def _plain_headers(headers: HeadersType) -> dict[str, str] | None:
    """Drop ``None`` header values for plain ``requests``.

    curl_cffi treats a ``None`` value as "suppress this default header", which
    is why HeadersType allows it. requests has no such concept and its stubs
    reject it, so the Legacy* retrievers strip those entries instead.
    """
    if headers is None:
        return None
    return {key: value for key, value in headers.items() if value is not None}


class RetrieverFunc(Protocol):
    """A callable that fetches a raw HTTP response for a source.

    This is the structural contract every retriever satisfies: a callable
    taking the source and returning a raw HTTP response. It carries only the
    ``__call__`` member so that a source can override ``retrieve`` with either a
    configured retriever instance or a plain ``def retrieve(self, source)``
    method without tripping ``reportIncompatibleVariableOverride``.
    """

    def __call__(self, source: BaseSource) -> Response: ...


class _BaseRetriever:
    """Concrete base for the configured HTTP retrievers.

    Provides the shared ``_resolve`` helper. The configured retriever classes
    inherit from this; service-specific retrievers that don't need ``_resolve``
    subclass :class:`RetrieverFunc` (the protocol) directly.
    """

    def _resolve(self, mapping: Callable[..., T] | T, source: BaseSource) -> T:
        """Resolve a constructor argument against the source's params.

        If ``mapping`` is callable, call it with ``**source.params`` so a
        source's user-supplied arguments flow into the URL/params/headers.
        Otherwise return the literal value.
        """
        if callable(mapping):
            return cast("T", mapping(**source.params))
        return cast("T", mapping)


class HttpGetRetriever(_BaseRetriever):
    """HTTP GET using curl_cffi (browser impersonation).

    Works on both regular endpoints and Cloudflare-protected sites. Each
    constructor argument may be a literal or a callable resolved against
    ``source.params``.
    """

    def __init__(
        self,
        url: UrlArgs,
        params: ParamsArgs = None,
        headers: HeadersArgs = None,
        timeout: int = 30,
    ):
        self.url = url
        self.params = params
        self.headers = headers
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        return source.session.get(
            self._resolve(self.url, source),
            params=self._resolve(self.params, source),
            headers=self._resolve(self.headers, source),
            timeout=self.timeout,
        )


class HttpPostRetriever(_BaseRetriever):
    """HTTP POST using curl_cffi (browser impersonation).

    Works on both regular endpoints and Cloudflare-protected sites. Each
    constructor argument may be a literal or a callable resolved against
    ``source.params``.
    """

    def __init__(
        self,
        url: UrlArgs,
        params: ParamsArgs = None,
        data: AnyArgs = None,
        json: JsonArgs = None,
        headers: HeadersArgs = None,
        timeout: int = 30,
    ):
        self.url = url
        self.params = params
        self.data = data
        self.json = json
        self.headers = headers
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        return source.session.post(
            self._resolve(self.url, source),
            params=self._resolve(self.params, source),
            data=self._resolve(self.data, source),
            json=self._resolve(self.json, source),
            headers=self._resolve(self.headers, source),
            timeout=self.timeout,
        )


class TwoStepRetriever(_BaseRetriever):
    """Resolve a key via a lookup request, then fetch the schedule with it.

    The common "address/postcode -> id -> collections" shape, used by ~50
    sources that currently hand-roll a two-request ``retrieve``. Provide:

    * ``lookup_url`` -- the lookup URL (or a callable resolved against
      ``source.params``), requested when no direct key is available;
    * ``extract`` -- ``callable(lookup_response, source) -> key``; it pulls the
      key out of the lookup response and may raise ``SourceArgumentNotFound`` /
      ``SourceArgumentNotFoundWithSuggestions`` to report a bad lookup;
    * ``schedule_url`` -- ``callable(key, **source.params) -> str`` for the
      final schedule request;
    * ``direct_key`` (optional) -- ``callable(source) -> key | None``; when it
      returns a key the lookup is skipped (e.g. the user supplied the id
      directly).

    Both requests use the shared ``source.session`` (curl_cffi)::

        retrieve = retrievers.TwoStepRetriever(
            lookup_url=lambda postcode, **_: f"{LOOKUP}/{postcode}",
            extract=_pick_uprn,
            schedule_url=lambda key, **_: f"{COLLECTIONS}/{key}",
            direct_key=lambda source: source.params.get("uprn"),
        )
    """

    def __init__(
        self,
        *,
        lookup_url: UrlArgs,
        extract: Callable[..., Any],
        schedule_url: Callable[..., str],
        direct_key: Callable[[BaseSource], Any] | None = None,
        headers: HeadersArgs = None,
    ):
        self.lookup_url = lookup_url
        self.extract = extract
        self.schedule_url = schedule_url
        self.direct_key = direct_key
        self.headers = headers

    def __call__(self, source: BaseSource) -> Response:
        # Same headers on both calls; e.g. an Accept: application/json that some
        # content-negotiating APIs need to return JSON rather than XML.
        headers = self._resolve(self.headers, source)
        key = self.direct_key(source) if self.direct_key else None
        if key is None:
            lookup = source.session.get(
                self._resolve(self.lookup_url, source), headers=headers
            )
            key = self.extract(lookup, source)
        return source.session.get(
            self.schedule_url(key, **source.params), headers=headers
        )


class LookupChainRetriever(_BaseRetriever):
    """Narrow an address through successive lookups, then fetch the schedule.

    :class:`TwoStepRetriever` generalised past a single lookup, for a provider
    whose address resolves one level at a time: municipality, then the street
    within that municipality, then whatever comes below it. Each level's answer
    is the input to the next, so the lookups cannot be issued in parallel or
    folded into one request.

    Each entry in ``steps`` is a ``callable(source, keys) -> key``, where
    ``keys`` is the tuple of ids resolved so far. The step issues whatever
    requests it needs through ``source.session`` and raises
    ``SourceArgumentNotFound*`` / ``SourceArgAmbiguous*`` for a level that did
    not resolve. The step owns its request rather than the retriever templating
    it because these lookups vary too much to template: one level is a POST with
    form data, the next a GET with query params, each with its own matching and
    normalisation rules.

    A key is whatever the next request needs, not necessarily an id. A level
    that yields several values at once returns them together (verl_de reads a
    middleware key and a page id off one page, as a NamedTuple, because a
    second step would mean a second identical GET), and a level whose answer
    *is* the download address returns that, leaving ``url`` to hand it straight
    back (``url=lambda *keys, **_: keys[-1]``, as kwu_de does with a scraped
    link).

    The schedule request is built from every resolved key, positionally, plus
    the source's params. It is a GET by default::

        retrieve = retrievers.LookupChainRetriever(
            steps=(_resolve_municipality, _resolve_street),
            url=f"{API}/content.php",
            params=lambda municipality_id, street_id, **_: {
                "GemeindeID": municipality_id,
                "StreetID": street_id,
            },
        )

    and a POST when the calendar is behind a download form rather than a URL,
    which is just as common on the German municipal platforms::

        retrieve = retrievers.LookupChainRetriever(
            steps=(_resolve_street,),
            url=CALENDAR_URL,
            method="POST",
            data=lambda street_id, house_number, **_: {
                "strasse": street_id,
                "hausnr": house_number,
            },
        )

    Args:
        steps: the ordered lookups. Must not be empty.
        url: the schedule URL: a literal, or
            ``callable(*keys, **source.params) -> str`` when an id goes in the
            path.
        params: optional ``callable(*keys, **source.params) -> params``, for the
            (at least as common) case of the ids going in the query string.
            Applies to a POST too, where a provider splits its ids between the
            query string and the form body.
        method: ``"GET"`` (default) or ``"POST"`` for the schedule request.
        data: optional ``callable(*keys, **source.params) -> data`` form body,
            for ``method="POST"``.
        headers: optional headers for the schedule request.
        encoding: response encoding forced on the schedule response before its
            ``.text`` is read. ``None`` (default) leaves the transport's
            auto-detected encoding alone; several providers mis-declare their
            charset and corrupt umlauts otherwise.
        raise_for_status: raise on an error status instead of handing the error
            body to the parser. Off by default so the existing callers are
            unaffected.
        timeout: schedule-request timeout in seconds.
    """

    def __init__(
        self,
        *,
        steps: Sequence[Callable[[BaseSource, tuple], Any]],
        url: UrlArgs,
        params: Callable[..., ParamsType] | None = None,
        method: str = "GET",
        data: Callable[..., Any] | None = None,
        headers: HeadersArgs = None,
        encoding: str | None = None,
        raise_for_status: bool = False,
        timeout: int = 30,
    ):
        if not steps:
            raise ValueError("LookupChainRetriever requires at least one step")
        if method.upper() not in ("GET", "POST"):
            raise ValueError(
                f"unknown LookupChainRetriever method {method!r}: expected GET or POST"
            )
        if data is not None and method.upper() != "POST":
            raise ValueError("LookupChainRetriever data requires method='POST'")
        self.steps = steps
        self.url = url
        self.params = params
        self.method = method.upper()
        self.data = data
        self.headers = headers
        self.encoding = encoding
        self.raise_for_status = raise_for_status
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        keys: tuple[Any, ...] = ()
        for step in self.steps:
            keys = (*keys, step(source, keys))

        url = self.url(*keys, **source.params) if callable(self.url) else self.url
        params = (
            self.params(*keys, **source.params) if self.params is not None else None
        )
        headers = self._resolve(self.headers, source)

        if self.method == "POST":
            response = source.session.post(
                url,
                params=params,
                data=(
                    self.data(*keys, **source.params) if self.data is not None else None
                ),
                headers=headers,
                timeout=self.timeout,
            )
        else:
            response = source.session.get(
                url, params=params, headers=headers, timeout=self.timeout
            )

        if self.raise_for_status:
            response.raise_for_status()
        if self.encoding is not None:
            response.encoding = self.encoding
        return response


class FanOutRetriever(_BaseRetriever):
    """Fetch one response per target and return them all.

    :class:`YearlyRetriever` fans out over years; this fans out over whatever
    the provider splits its calendar by. A municipality that publishes one ICS
    feed per waste type (four rounds, four downloads) has no single response to
    retrieve, and the list of feeds is usually not known until an address has
    been resolved. Returns a *list* of responses, so pair it with
    :class:`~waste_collection_schedule.parsers.EachResponse` around whatever
    parser reads one::

        retrieve = retrievers.FanOutRetriever(
            prepare=_resolve_area,
            targets=lambda source, area: _feed_urls(source, area),
        )
        parse = parsers.EachResponse(parsers.IcsParser())

    Args:
        targets: ``callable(source, context) -> Sequence`` listing what to
            fetch, one response each. ``context`` is whatever ``prepare``
            returned, or ``None`` when there is no ``prepare``. Usually a list
            of URLs, but any value ``fetch`` understands will do.
        prepare: optional ``callable(source) -> context``, run once before the
            targets are listed. This is where an address is resolved to the ids
            (or the session state) the feeds need, so that lookup happens once
            rather than once per feed.
        fetch: optional ``callable(source, target, context) -> Response``,
            issuing the request for one target through ``source.session``.
            Defaults to a plain GET of the target as a URL; pass one when the
            requests need cookies or headers carried over from ``prepare``. It
            may return ``None`` for a target that has nothing for this
            household, which is dropped rather than reaching the parser: a
            platform publishing one calendar per year tends to have gaps around
            a boundary year, and a missing year is not a failed fetch.
    """

    def __init__(
        self,
        *,
        targets: Callable[[BaseSource, Any], Sequence[Any]],
        prepare: Callable[[BaseSource], Any] | None = None,
        fetch: Callable[[BaseSource, Any, Any], Response | None] | None = None,
    ):
        self.targets = targets
        self.prepare = prepare
        self.fetch = fetch

    def __call__(self, source: BaseSource) -> list[Response]:
        context = self.prepare(source) if self.prepare is not None else None
        responses = (
            (
                self.fetch(source, target, context)
                if self.fetch is not None
                else source.session.get(target)
            )
            for target in self.targets(source, context)
        )
        return [response for response in responses if response is not None]


class FirstMatchRetriever(_BaseRetriever):
    """Try interchangeable candidate requests; keep the first that answers.

    For a provider that serves one address's calendar from more than one place
    and will only tell you which of them is live by answering: a load-balanced
    pair of hosts, a per-year path where next year's file appears at its own
    time, or, as with karlsruhe_de, both axes at once. The candidates are
    equivalent, so unlike :class:`LookupChainRetriever` there is nothing to
    resolve up front, and unlike :class:`FanOutRetriever` (which fetches every
    target and keeps them all) the search stops at the first response that is
    the calendar.

    The same idea already sits in two narrow, hard-coded forms elsewhere:
    :class:`AthosWasteManagementRetriever`'s ``fallback_url`` (a second URL
    tried when the first 404s) and the ICS platform's
    ``IcsYearRetriever.fallback_url`` (a second URL tried when the first came
    back empty). This is that pattern with the candidate list left open and the
    acceptance test named.

    Mechanics: build and issue the request for each candidate in turn. A
    candidate that raises (DNS, TLS, timeout) is skipped and its error
    remembered. The first response ``accept`` returns True for is returned. If
    no candidate is accepted, the last response received is returned anyway, so
    the parser's own shape check reports what the provider actually said rather
    than a bare transport error; only if every candidate raised is the last
    error re-raised::

        retrieve = retrievers.FirstMatchRetriever(
            candidates=_years_by_host,
            url=lambda candidate, **_: API_URL.format(
                year=candidate[0], i=candidate[1]
            ),
            method="POST",
            data=lambda candidate, street, **_: {"strasse_n": street},
            accept=_has_events,
        )

    Args:
        candidates: what to try, in order, as ``callable(**source.params) ->
            Sequence`` or a literal sequence. A candidate is whatever the
            request template needs: a URL, a year, a (year, host) pair. An
            empty list is a configuration error, and raises.
        url: the request URL, as ``callable(candidate, **source.params) -> str``
            or a literal (for candidates that vary only the body).
        accept: ``callable(response) -> bool``, deciding whether a response is
            the real calendar rather than the empty stand-in an unserved
            candidate returns. Required, and deliberately not defaulted: what
            "unserved" looks like is provider knowledge, and a wrong guess here
            silently settles on the wrong host.
        method: ``"GET"`` (default) or ``"POST"``.
        params: optional query arguments, as
            ``callable(candidate, **source.params)`` or a literal.
        data: optional form body for ``method="POST"``, same calling
            convention.
        headers: optional headers, same calling convention.
        timeout: per-request timeout in seconds.
    """

    def __init__(
        self,
        *,
        candidates: Callable[..., Sequence[Any]] | Sequence[Any],
        url: Callable[..., str] | str,
        accept: Callable[[Response], bool],
        method: str = "GET",
        params: Callable[..., ParamsType] | ParamsType = None,
        data: Callable[..., Any] | Any = None,
        headers: Callable[..., HeadersType] | HeadersType = None,
        timeout: int = 30,
    ):
        if method.upper() not in ("GET", "POST"):
            raise ValueError(
                f"unknown FirstMatchRetriever method {method!r}: expected GET or POST"
            )
        if data is not None and method.upper() != "POST":
            raise ValueError("FirstMatchRetriever data requires method='POST'")
        self.candidates = candidates
        self.url = url
        self.accept = accept
        self.method = method.upper()
        self.params = params
        self.data = data
        self.headers = headers
        self.timeout = timeout

    def _for(self, mapping: Callable[..., T] | T, candidate: Any, source: BaseSource):
        """Resolve a per-candidate argument: the candidate, then the params."""
        if callable(mapping):
            return mapping(candidate, **source.params)
        return mapping

    def _request(self, source: BaseSource, candidate: Any) -> Response:
        url = self._for(self.url, candidate, source)
        params = self._for(self.params, candidate, source)
        headers = self._for(self.headers, candidate, source)
        if self.method == "POST":
            return source.session.post(
                url,
                params=params,
                data=self._for(self.data, candidate, source),
                headers=headers,
                timeout=self.timeout,
            )
        return source.session.get(
            url, params=params, headers=headers, timeout=self.timeout
        )

    def __call__(self, source: BaseSource) -> Response:
        candidates = list(self._resolve(self.candidates, source))
        if not candidates:
            raise ValueError("FirstMatchRetriever was given no candidates to try")

        last_response: Response | None = None
        last_error: Exception | None = None
        for candidate in candidates:
            try:
                response = self._request(source, candidate)
            # A candidate that cannot even be reached is simply not the live
            # one; the next candidate is the whole point of the list.
            except Exception as error:
                last_error = error
                continue
            last_response = response
            if self.accept(response):
                return response

        if last_response is not None:
            return last_response
        raise cast("Exception", last_error)


class Branch(NamedTuple):
    """One alternative feed for :class:`FallbackRetriever`.

    Args:
        label: names the branch. :class:`~waste_collection_schedule.parsers.FirstNonEmptyBranch`
            reads it to pick the parser for whatever this branch came back with,
            so the two sides agree on the branch's shape without the retriever
            knowing how it is parsed.
        fetch: issues this branch's request(s). Called as ``fetch(source)``, or
            as ``fetch(source, context)`` when the retriever has a ``prepare``
            step. With no ``prepare``, any ordinary retriever instance is a
            valid ``fetch`` unchanged.
        when: optional ``callable(**source.params) -> bool``. A branch the user
            has not configured (they supplied the other feed's arguments) is
            skipped without a request, rather than being asked a question it
            has no key for.
    """

    label: Any
    fetch: Callable[..., Any]
    when: Callable[..., bool] | None = None


class Attempt(NamedTuple):
    """What one :class:`Branch` came back with: its raw data, or its error."""

    label: Any
    raw: Any = None
    error: Exception | None = None


def reuse_prepared(source: BaseSource, context: Any) -> Any:
    """Branch fetch that re-reads what ``prepare`` already fetched, issuing nothing.

    For the case where the fallback is not a second request at all but a second
    reading of the page the first branch was found on: the page carries a short
    preview of the schedule *and* a link to the full feed, so when the feed is
    unavailable the preview already in hand is the fallback.
    """
    return context


def follow_link(
    pattern: str,
    *,
    selector: str = "a",
    attribute: str = "href",
    timeout: int = 30,
) -> Callable[..., Response]:
    """Branch fetch: GET the first link on the prepared page whose href matches.

    The "the page tells you where the real feed is" step, for a provider that
    mints the calendar's URL per address or per week and links to it from the
    address's page. The link is resolved against the page's own URL, so a
    relative href works. Nothing matching the pattern raises, which a
    :class:`FallbackRetriever` treats as this branch not working out::

        retrieve = retrievers.FallbackRetriever(
            retrievers.Branch("ics", retrievers.follow_link(r"\\.ics$")),
            retrievers.Branch("page", retrievers.reuse_prepared),
            prepare=_collection_page,
        )

    Args:
        pattern: regex searched against the attribute's value.
        selector: CSS selector for the candidate elements (default ``"a"``).
        attribute: the attribute holding the URL (default ``"href"``).
        timeout: request timeout in seconds.
    """
    compiled = re.compile(pattern)

    def fetch(source: BaseSource, context: Any) -> Response:
        soup = BeautifulSoup(context.text, "html.parser")
        for tag in soup.select(selector):
            value = tag.get(attribute)
            if isinstance(value, str) and compiled.search(value):
                return source.session.get(
                    urljoin(getattr(context, "url", "") or "", value), timeout=timeout
                )
        raise LookupError(
            f"no {selector}[{attribute}] matching {pattern!r} on the retrieved page"
        )

    return fetch


class FallbackRetriever(_BaseRetriever):
    """Try alternative feeds in order, stopping at the first that has the schedule.

    :class:`FirstMatchRetriever` chooses between interchangeable *requests*: one
    URL template, one parser, one ``accept`` test on the raw response. This
    chooses between whole *feeds* — an unofficial community API and the
    council's official map server, or a downloadable calendar and the preview
    already rendered on the page that links to it. They answer in different
    shapes, so each branch brings its own parser, and whether a branch worked
    out is only knowable once it has been parsed.

    That makes the decision span retrieve and parse, so retrieve hands over a
    *lazy* stream of :class:`Attempt`s and
    :class:`~waste_collection_schedule.parsers.FirstNonEmptyBranch` drives it —
    the same arrangement a paginating parser already uses to control how much of
    a lazy retriever it consumes. A later branch is never requested when an
    earlier one answered::

        retrieve = retrievers.FallbackRetriever(
            retrievers.Branch("community", _COMMUNITY_FEED, when=_has_record_id),
            retrievers.Branch("official", _OFFICIAL_LAYERS, when=_has_object_ids),
        )
        parse = parsers.FirstNonEmptyBranch(
            {"community": parsers.LabelledSections(...), "official": ArcGisMultiFeatureParser()}
        )

    A branch that raises is reported as a failed attempt rather than aborting
    the fetch, so an outage on the preferred feed falls through to the next one.
    The last branch attempted has the last word: if no branch produced records,
    its error (or its empty result) is what the source sees, so the user hears
    about the feed that was actually meant to serve them.

    Args:
        *branches: the :class:`Branch`es to try, in order. At least one is
            required; an empty list is a configuration error and raises.
        prepare: optional ``callable(source) -> context``, run once before any
            branch. This is where shared state is fetched exactly once — a
            resolved address, or the page both branches read — instead of each
            branch repeating it. When given, each branch's ``fetch`` is called
            as ``fetch(source, context)``; without it, as ``fetch(source)``.
    """

    def __init__(
        self,
        *branches: Branch,
        prepare: Callable[[BaseSource], Any] | None = None,
    ):
        if not branches:
            raise ValueError("FallbackRetriever was given no branches to try")
        self.branches = branches
        self.prepare = prepare

    def _fetch(self, branch: Branch, source: BaseSource, context: Any) -> Any:
        if self.prepare is not None:
            return branch.fetch(source, context)
        return branch.fetch(source)

    def _attempts(self, source: BaseSource, context: Any) -> Iterator[Attempt]:
        for branch in self.branches:
            if branch.when is not None and not branch.when(**source.params):
                continue
            try:
                raw = self._fetch(branch, source, context)
            # A branch that cannot be reached has not answered; the next branch
            # is the whole point of the list.
            except Exception as error:
                _LOGGER.debug(
                    "FallbackRetriever: branch %r did not answer: %s",
                    branch.label,
                    error,
                )
                yield Attempt(branch.label, None, error)
                continue
            yield Attempt(branch.label, raw, None)

    def __call__(self, source: BaseSource) -> Iterator[Attempt]:  # type: ignore[override]
        # prepare runs eagerly (it is this retriever's own request); the
        # branches are pulled by the parser, one at a time.
        context = self.prepare(source) if self.prepare is not None else None
        return self._attempts(source, context)


#: Default pattern for the JS chunks a Next.js page loads. Group 1 is the
#: chunk's href, resolved against the page URL; any ``?v=`` cache-buster after
#: the ``.js`` is dropped so the same chunk is only fetched once.
NEXT_CHUNK_PATTERN = r'src="([^"]*/_next/static/chunks/[^"?]+\.js)(?:\?[^"]*)?"'


class NextActionRetriever(_BaseRetriever):
    """Call a Next.js "server action", then fetch the schedule with its result.

    Same two-step shape as :class:`TwoStepRetriever` (lookup -> key -> schedule)
    for sites whose address search is a React Server Component *server action*
    rather than a documented REST endpoint. There is no stable URL to call: the
    action is addressed by a 40+ hex-character id that Next.js mints at build
    time and only ever emits inside the page's JS bundle, so it has to be read
    out of the bundle and changes with every deployment.

    Mechanics:

    1. GET ``page_url`` and collect the JS chunk hrefs it loads
       (``chunk_pattern``, resolved against the page URL).
    2. GET each chunk and regex out every action id tagged with ``action_name``.
       Several stale ids from older deployments usually sit alongside the
       current one, and a chunk that fails to download is skipped.
    3. POST ``arguments`` to ``page_url`` as a JSON array with the
       ``next-action`` header set to a candidate id, until one is accepted
       (HTTP 200). The winning id is remembered on the source instance, so a
       long-lived source (Home Assistant re-polls the same instance) skips the
       bundle scan on later fetches.
    4. Decode the RSC "flight" line prefixed ``result_prefix`` into the action's
       return value, hand it to ``extract`` to pull out the key, and GET
       ``schedule_url(key, **source.params)``.

    ``extract`` receives ``None`` when no candidate id was accepted or no result
    line came back, so a source can raise its own ``SourceArgumentNotFound*``
    for a bad address rather than a bare transport error::

        retrieve = retrievers.NextActionRetriever(
            page_url=BASE_URL,
            action_name="searchAddressAction",
            arguments=lambda street, house_number, **_: [f"{street} {house_number}"],
            extract=_first_address_id,
            schedule_url=lambda key, **_: f"{BASE_URL}/{key}/calendar.ics",
            direct_key=lambda source: source.params.get("uuid"),
        )

    Args:
        page_url: the page hosting the action; also the POST target (literal or
            ``callable(**source.params) -> str``).
        action_name: the exported action's name as it appears in the bundle,
            e.g. ``"searchAddressAction"``.
        arguments: the action's argument array (literal, or
            ``callable(**source.params) -> list``), sent as the JSON body.
        extract: ``callable(result, source) -> key``; ``result`` is the decoded
            action return value, or ``None`` if the call did not succeed.
        schedule_url: ``callable(key, **source.params) -> str`` for the final GET.
        direct_key: optional ``callable(source) -> key | None``; when it returns
            a key the whole action dance is skipped (the user supplied the id).
        chunk_pattern: regex whose group 1 is a JS chunk href
            (default :data:`NEXT_CHUNK_PATTERN`).
        result_prefix: the flight-line prefix carrying the return value
            (default ``"1:"``).
        headers: optional extra headers merged into every request.
        timeout: per-request timeout in seconds.
    """

    def __init__(
        self,
        *,
        page_url: UrlArgs,
        action_name: str,
        arguments: Callable[..., list] | list,
        extract: Callable[..., Any],
        schedule_url: Callable[..., str],
        direct_key: Callable[[BaseSource], Any] | None = None,
        chunk_pattern: str = NEXT_CHUNK_PATTERN,
        result_prefix: str = "1:",
        headers: HeadersArgs = None,
        timeout: int = 30,
    ):
        self.page_url = page_url
        self.action_name = action_name
        self.arguments = arguments
        self.extract = extract
        self.schedule_url = schedule_url
        self.direct_key = direct_key
        self.chunk_pattern = re.compile(chunk_pattern)
        self.action_pattern = re.compile(
            r'"([0-9a-f]{40,})"[\s\S]{0,120}?' + re.escape(action_name)
        )
        self.result_prefix = result_prefix
        self.headers = headers
        self.timeout = timeout
        # A retriever is a class attribute shared by every instance of the
        # source, so the scan results are kept per source instance (weakly, so
        # a discarded source is not held alive by its cache entry).
        self._cache_by_source: WeakKeyDictionary[BaseSource, dict[str, Any]] = (
            WeakKeyDictionary()
        )

    def _cache(self, source: BaseSource) -> dict[str, Any]:
        """Per-source-instance store for the bundle scan's results."""
        cache = self._cache_by_source.get(source)
        if cache is None:
            cache = {"candidates": None, "winner": None}
            self._cache_by_source[source] = cache
        return cache

    def _candidates(
        self, source: BaseSource, page_url: str, headers: HeadersType
    ) -> list[str]:
        cache = self._cache(source)
        if cache["candidates"] is not None:
            return cache["candidates"]

        page = source.session.get(page_url, headers=headers, timeout=self.timeout)
        page.raise_for_status()

        candidates: list[str] = []
        for href in dict.fromkeys(self.chunk_pattern.findall(page.text)):
            try:
                chunk = source.session.get(
                    urljoin(page_url, href), headers=headers, timeout=self.timeout
                )
                chunk.raise_for_status()
            # A single unavailable chunk must not sink the whole lookup: the
            # action id is only ever in one of them, and which one varies.
            except Exception:
                continue
            for match in self.action_pattern.finditer(chunk.text):
                if match.group(1) not in candidates:
                    candidates.append(match.group(1))

        cache["candidates"] = candidates
        return candidates

    def _invoke(
        self,
        source: BaseSource,
        page_url: str,
        action: str,
        body: str,
        headers: HeadersType,
    ) -> Any:
        response = source.session.post(
            page_url,
            headers={
                "content-type": "text/plain;charset=UTF-8",
                "accept": "text/x-component",
                "next-action": action,
                **(headers or {}),
            },
            data=body,
            timeout=self.timeout,
        )
        if response.status_code != 200:
            return None
        for line in response.text.splitlines():
            if line.startswith(self.result_prefix):
                return json.loads(line[len(self.result_prefix) :])
        return None

    def _call_action(
        self, source: BaseSource, page_url: str, headers: HeadersType
    ) -> Any:
        body = json.dumps(self._resolve(self.arguments, source))
        cache = self._cache(source)

        candidates = self._candidates(source, page_url, headers)
        winner = cache["winner"]
        if winner and winner in candidates:
            candidates = [winner] + [c for c in candidates if c != winner]

        for action in candidates:
            result = self._invoke(source, page_url, action, body, headers)
            if result is not None:
                cache["winner"] = action
                return result
        return None

    def __call__(self, source: BaseSource) -> Response:
        headers = self._resolve(self.headers, source)
        page_url = self._resolve(self.page_url, source)

        key = self.direct_key(source) if self.direct_key else None
        if key is None:
            key = self.extract(self._call_action(source, page_url, headers), source)

        schedule = source.session.get(
            self.schedule_url(key, **source.params),
            headers=headers,
            timeout=self.timeout,
        )
        schedule.raise_for_status()
        return schedule


class PdfLinkRetriever(_BaseRetriever):
    """Find a document link on an HTML index page, then download it.

    For a provider whose calendar file (typically a PDF) is linked from a
    stable landing page under a URL that rotates -- usually per year, often on
    an opaque host or hashed path. Rather than hardcode a URL that breaks every
    January, this fetches the index page, scans its ``<a href>`` values for
    ``pattern``, picks one, resolves it against the index URL, and GETs it. Both
    requests use the shared curl_cffi session.

    Like :class:`TwoStepRetriever` this reads the first response's body (to find
    the link); that is the sanctioned exception to "a retriever only does HTTP".

        retrieve = retrievers.PdfLinkRetriever(
            index_url="https://www.berdorf.lu/service-citoyens/dechets",
            pattern=r"offallkalenner-(\\d{4})\\.pdf",
        )

    The chosen PDF's URL travels back on the returned response (``response.url``),
    so a parser can read the calendar year off it without a second lookup.

    Args:
        index_url: the stable landing page (literal or
            ``callable(**source.params) -> str``).
        pattern: regex searched against each ``href`` (case-insensitive). A
            capturing group's text drives ``select`` (typically a 4-digit year);
            without a group, ``select`` sees the whole matched href.
        select: which match to keep when several hrefs match. ``"newest_current"``
            (default): read the captured group as an int and pick the largest
            that is ``>=`` the current year, so a future calendar wins and a
            stale past-year link is ignored (falls back to the newest overall if
            none are current). ``"max"``: largest captured int overall.
            ``"first"``: first in document order. Or a
            ``callable(list[re.Match]) -> re.Match``.
        headers: optional headers applied to both requests.
        timeout: per-request timeout in seconds.
    """

    def __init__(
        self,
        *,
        index_url: UrlArgs,
        pattern: str,
        select: str | Callable[[list[re.Match]], re.Match] = "newest_current",
        headers: HeadersArgs = None,
        timeout: int = 30,
    ):
        self.index_url = index_url
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.select = select
        self.headers = headers
        self.timeout = timeout

    @staticmethod
    def _captured_int(match: re.Match) -> int | None:
        try:
            return int(match.group(1))
        except (IndexError, ValueError):
            return None

    def _choose(self, matches: list[re.Match]) -> re.Match:
        if callable(self.select):
            return self.select(matches)
        if self.select == "first":
            return matches[0]
        keyed = [(self._captured_int(m), m) for m in matches]
        valid = [(value, m) for value, m in keyed if value is not None]
        if self.select == "max":
            return max(valid, key=lambda vm: vm[0])[1] if valid else matches[0]
        if self.select == "newest_current":
            current_year = datetime.date.today().year
            current = [(value, m) for value, m in valid if value >= current_year]
            if current:
                return max(current, key=lambda vm: vm[0])[1]
            # No current-or-future link: fall back to the newest we saw.
            return max(valid, key=lambda vm: vm[0])[1] if valid else matches[0]
        raise ValueError(f"unknown PdfLinkRetriever select strategy {self.select!r}")

    def __call__(self, source: BaseSource) -> Response:
        headers = self._resolve(self.headers, source)
        index_url = self._resolve(self.index_url, source)

        index = source.session.get(index_url, headers=headers, timeout=self.timeout)
        index.raise_for_status()

        soup = BeautifulSoup(index.text, "html.parser")
        matches = [
            match
            for tag in soup.find_all("a", href=True)
            if (match := self.pattern.search(str(tag["href"])))
        ]
        if not matches:
            raise ValueError(
                f"no link matching {self.pattern.pattern!r} found on {index_url}; "
                "the page layout may have changed."
            )

        pdf_url = urljoin(index_url, self._choose(matches).string)
        pdf = source.session.get(pdf_url, headers=headers, timeout=self.timeout)
        pdf.raise_for_status()
        return pdf


# One step of an AthosWasteManagementRetriever wizard: a dict with keys
#
#   submit_action -- (required) the ``SubmitAction`` form value posted for
#       this step: a literal str, or ``callable(**source.params) -> str``.
#   fields        -- (optional) ``callable(**source.params) -> dict[str, Any]``
#       returning field overrides/additions merged into the running form
#       state before this step's POST. Omit for a step that only advances
#       ``SubmitAction`` (e.g. a plain "forward").
#   remove        -- (optional) iterable of field names dropped from the
#       running state before this step's POST (a step that must not resend
#       fields an earlier step set, e.g. the final step of the bmv_at
#       variant).
#   reset         -- (optional) True to empty the running state before this
#       step's `fields` are applied, so the step posts only its own fields
#       (a deployment whose download step takes a fresh two-field payload
#       rather than the whole accumulated form, e.g. zakb_de).
#
# Not a TypedDict: `submit_action` is required while the rest are not, and
# PEP 655 Required/NotRequired needs a newer typing than this module's
# pyright target -- a plain dict keeps step access unchecked but simple; see
# AthosWasteManagementRetriever's docstring for the worked shape.
type AthosStep = "dict[str, Any]"


def _scrape_hidden_inputs(html: str) -> dict[str, str]:
    """Return ``{name: value}`` for every ``<input type=hidden>`` in ``html``.

    Shared by every Athos "WasteManagementServlet" deployment to seed the
    wizard's form state from the initial GET. Matches ``type`` case-
    insensitively: most deployments emit lowercase ``hidden``, at least one
    (bmv_at) emits uppercase ``HIDDEN``.
    """
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, str] = {}
    for tag in soup.find_all("input"):
        if str(tag.get("type", "")).lower() != "hidden":
            continue
        name = tag.get("name")
        if name:
            fields[str(name)] = str(tag.get("value", ""))
    return fields


class AthosWasteManagementRetriever(_BaseRetriever):
    """Data-driven engine for the Athos "WasteManagementServlet" wizard.

    Shared mechanics behind ~15 German/Austrian providers (awn_de, bielefeld_de,
    bmv_at, ...): an initial GET returns a page seeded with ``<input
    type=hidden>`` form state; the site then advances through a small, fixed
    number of POSTs (changing city/street, selecting containers, ...) before a
    final POST downloads the ICS calendar. Every deployment follows the same
    request/response shape; only the field names, field values and number of
    steps differ (see the bmv_at variant, which uses ``Focus``-driven steps
    instead of ``CITYCHANGED``/``STREETCHANGED``/``forward``). The whole flow
    is therefore expressed as data (``steps``), not per-source control flow.

    Mechanics:

    1. GET ``url`` with ``initial_params``. If it 404s and ``fallback_url`` is
       set, retry there instead (a servlet that moved host/path while old
       deployments still link the previous one).
    2. Scrape the response's ``<input type=hidden>`` fields into the running
       form state (the wizard's server-side session key/values). See
       ``state`` for the two deployments that seed it differently.
    3. For each entry in ``steps`` (in order): merge ``fields(**source.params)``
       into the running state, drop any ``remove`` keys, set the submit-action
       field (``SubmitAction`` by default) to ``submit_action`` (resolved
       against ``source.params`` if callable), then POST the accumulated state
       back to the servlet URL.
    4. Return the *last* step's response (the ICS download) unparsed; pair
       with ``parsers.IcsParser()`` / ``parsers.IcsEventsParser()``.

    The form state accumulates across steps (a later step inherits every
    earlier step's fields unless a step's ``remove`` drops them, or its
    ``reset`` empties it) because the servlet is itself stateless between
    POSTs — the growing form *is* the session.

    Example (the awn_de shape: one field-setting step, one container-selection
    step, one download step)::

        retrieve = AthosWasteManagementRetriever(
            url="https://athos.awn-online.de/WasteManagementNeckarOdenwald/WasteManagementServlet",
            initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
            steps=[
                {
                    "submit_action": "CITYCHANGED",
                    "fields": lambda city, street, house_number, address_suffix="", **_: {
                        "Ort": city,
                        "Strasse": street,
                        "Hausnummer": str(house_number),
                        "Hausnummerzusatz": address_suffix,
                    },
                },
                {
                    "submit_action": "forward",
                    "fields": lambda **_: {
                        f"ContainerGewaehlt_{i}": "on" for i in range(1, 8)
                    },
                },
                {
                    "submit_action": "filedownload_ICAL",
                    "fields": lambda **_: {
                        "ApplicationName": "com.athos.kd.neckarodenwald.abfuhrtermine.AbfuhrTerminModel",
                    },
                },
            ],
        )

    Args:
        url: the servlet URL (``callable(**source.params) -> str``, or a literal).
        steps: ordered list of :class:`AthosStep` dicts (see above). Must not
            be empty.
        initial_params: query params for the initial GET (default:
            ``{"SubmitAction": "wasteDisposalServices"}``).
        fallback_url: optional second URL (callable or literal), retried if
            the initial GET 404s.
        headers: optional headers applied to every request (GET and POST).
        encoding: response encoding forced on every response before reading
            ``.text`` (default ``"utf-8"``; several deployments mis-declare
            their charset, corrupting umlauts otherwise). Pass ``None`` to
            leave the transport's auto-detected encoding alone.
        submit_action_field: form field carrying the step's action (default
            ``"SubmitAction"``). A deployment fronted by a CMS rather than the
            servlet itself renames it (zakb_de posts ``submitAction``).
        state: how the running form state is seeded between steps.

            * ``"accumulate"`` (default) — scrape the hidden inputs of the
              initial GET once, then carry that state forward through every
              step, which is what most deployments here need.
            * ``"rescrape"`` — re-seed from *each step's own response* before
              the next POST, so the page's current ``ApplicationName`` /
              ``PageName`` / ``IsLastPage`` are echoed back rather than the
              values the wizard started with. This is what the servlet's own
              JavaScript does; deployments on ``"accumulate"`` compensate by
              naming those fields per step instead (see the awn_de example
              above).
            * ``"none"`` — never scrape; the state is only what the steps'
              ``fields`` put there. For a deployment whose page carries
              unrelated hidden inputs that must *not* be posted back (zakb_de
              sits inside a TYPO3 page whose hidden inputs are login-form
              tokens).

        verify: TLS verification for every request, passed straight to the
            session (default ``True``). ``False`` disables it; a path to a CA
            bundle uses that bundle instead. Needed by a deployment whose
            certificate is itself valid but whose server omits the issuing
            intermediate, so the chain cannot be built from the default trust
            store (awg_de). Prefer a completed bundle over ``False`` where the
            missing intermediate is known and stable.
    """

    def __init__(
        self,
        *,
        url: UrlArgs,
        steps: list[AthosStep],
        initial_params: ParamsType = None,
        fallback_url: UrlArgs | None = None,
        headers: HeadersArgs = None,
        encoding: str | None = "utf-8",
        submit_action_field: str = "SubmitAction",
        state: str = "accumulate",
        verify: bool | str = True,
    ):
        if not steps:
            raise ValueError("AthosWasteManagementRetriever requires at least one step")
        if state not in ("accumulate", "rescrape", "none"):
            raise ValueError(
                f"unknown Athos state mode {state!r}: "
                "expected 'accumulate', 'rescrape' or 'none'"
            )
        self.url = url
        self.steps = steps
        self.initial_params = (
            initial_params
            if initial_params is not None
            else {"SubmitAction": "wasteDisposalServices"}
        )
        self.fallback_url = fallback_url
        self.headers = headers
        self.encoding = encoding
        self.submit_action_field = submit_action_field
        self.state = state
        self.verify = verify

    def _apply_encoding(self, response: Response) -> Response:
        if self.encoding is not None:
            response.encoding = self.encoding
        return response

    def __call__(self, source: BaseSource) -> Response:
        headers = self._resolve(self.headers, source)
        url = self._resolve(self.url, source)

        initial = source.session.get(
            url, params=self.initial_params, headers=headers, verify=self.verify
        )
        if initial.status_code == 404 and self.fallback_url is not None:
            url = self._resolve(self.fallback_url, source)
            initial = source.session.get(
                url, params=self.initial_params, headers=headers, verify=self.verify
            )
        initial.raise_for_status()
        self._apply_encoding(initial)

        state: dict[str, Any] = (
            {} if self.state == "none" else _scrape_hidden_inputs(initial.text)
        )

        response = initial
        for index, step in enumerate(self.steps):
            # index 0 already holds the inputs of the initial GET, so only
            # the later steps need re-seeding from the page just received.
            if self.state == "rescrape" and index:
                state = _scrape_hidden_inputs(response.text)
            if step.get("reset"):
                state = {}
            state.update(step["fields"](**source.params) if "fields" in step else {})
            for key in step.get("remove", ()):
                state.pop(key, None)
            state[self.submit_action_field] = self._resolve(
                step["submit_action"], source
            )
            # A fresh copy per POST: state is mutated further by later steps,
            # and callers (session mocks in tests, request logging, retry
            # wrappers) may hold onto the `data` they were given rather than
            # consuming it immediately.
            response = source.session.post(
                url, data=dict(state), headers=headers, verify=self.verify
            )
            response.raise_for_status()
            self._apply_encoding(response)

        return response


class AthosNoticeFilter:
    """Drop the notice events an Athos calendar carries beside its collections.

    The servlet's ICS export can contain an announcement VEVENT rather than a
    collection: bielefeld_de's calendar carries one summarised "Die neue
    ICal...", which the transformer would otherwise publish as a waste type of
    its own. This is the preprocess half of the Athos platform, so declare it
    alongside :class:`AthosWasteManagementRetriever` on a deployment whose
    export carries one::

        retrieve = AthosWasteManagementRetriever(...)
        parse = parsers.IcsParser()
        preprocess = retrievers.AthosNoticeFilter()
        transform = ICSTransformer(type_value_map={...})

    Opt-in, and deliberately narrow: only one of the ~15 deployments here is
    known to emit a notice, so a source that does not declare this keeps the
    default preprocessor and is unaffected. ``marker`` is the substring that
    identifies the notice, defaulting to that deployment's wording, so a
    deployment wording its own notice differently passes its own marker rather
    than needing new code.

    Records are matched at index 1, which is the title in both record shapes an
    ICS parser yields: the ``(date, summary)`` tuple of ``parsers.IcsParser``
    and the ``IcsEvent(date, title, ...)`` of ``parsers.IcsEventsParser``.

    Satisfies the ``preprocessors.Preprocessor`` protocol structurally; it is
    not imported here, so this module keeps depending on nothing downstream of
    retrieve.
    """

    def __init__(self, marker: str = "Die neue ICal"):
        self.marker = marker

    def __call__(
        self, records: Iterable[Any], source: BaseSource | None = None
    ) -> Iterator[Any]:
        return (r for r in records if self.marker not in r[1])


class YearlyRetriever(_BaseRetriever):
    """Fetch one calendar per year, rolling into next year late in the year.

    For a provider that publishes a separate, year-scoped calendar: a
    ``/abfuhrtermine/2026/...`` page, or an ICS generator that takes a year as a
    form field. The current year is always fetched; from ``rollover_month`` the
    following year is fetched too, so a schedule polled on 28 December does not
    run dry on 1 January. That second fetch is best-effort, because the provider
    typically publishes next year's calendar some time during the rollover
    month and a 404 before then must not fail the whole retrieve.

    Returns a *list* of responses, so pair it with
    :class:`~waste_collection_schedule.parsers.EachResponse` around whatever
    parser reads one year::

        retrieve = retrievers.YearlyRetriever(
            prepare=_resolve_ids,
            fetch=_calendar_for_year,
            refresh_on_failure=True,
        )
        parse = parsers.EachResponse(parsers.IcsParser())

    Args:
        fetch: ``callable(source, year, context) -> Response``; issues the
            request for one year through ``source.session``. ``context`` is
            whatever ``prepare`` returned, or ``None`` when there is no
            ``prepare``. Raise to signal that year is unavailable.
        prepare: optional ``callable(source) -> context``, run once before the
            year fetches. This is where an address is resolved to the ids the
            calendar request needs, so that lookup happens once rather than
            once per year.
        rollover_month: calendar month (1-12) from and including which the
            following year is also attempted (default 12, December). Set it
            earlier for a provider that publishes early; pass ``None`` to fetch
            only the current year.
        refresh_on_failure: when True (and ``prepare`` is set), a failure of the
            year fetches re-runs ``prepare`` once and retries them. For a
            provider whose dropdown ids drift between polls, so a stale id is
            corrected rather than surfaced to the user as an error. Off by
            default: a retry doubles the request count on a genuinely broken
            endpoint.
    """

    def __init__(
        self,
        *,
        fetch: Callable[..., Response],
        prepare: Callable[[BaseSource], Any] | None = None,
        rollover_month: int | None = 12,
        refresh_on_failure: bool = False,
    ):
        self.fetch = fetch
        self.prepare = prepare
        self.rollover_month = rollover_month
        self.refresh_on_failure = refresh_on_failure

    def _all_years(self, source: BaseSource, context: Any) -> list[Response]:
        now = datetime.datetime.now()
        responses = [self.fetch(source, now.year, context)]
        if self.rollover_month is not None and now.month >= self.rollover_month:
            try:
                responses.append(self.fetch(source, now.year + 1, context))
            # Next year's calendar is routinely not up yet during the rollover
            # month; this year's is still a complete answer on its own.
            except Exception:
                pass
        return responses

    def __call__(self, source: BaseSource) -> Any:
        context = self.prepare(source) if self.prepare is not None else None
        try:
            return self._all_years(source, context)
        except Exception:
            if not (self.refresh_on_failure and self.prepare is not None):
                raise
            context = self.prepare(source)
            return self._all_years(source, context)


def submit_page_form(
    source: BaseSource,
    url: str,
    *,
    marker: str,
    base_url: str = "",
    encoding: str | None = None,
    headers: HeadersType = None,
) -> Response:
    """GET a page, scrape the form carrying ``marker``, and POST it straight back.

    For a download that sits behind a same-page form rather than a link: the
    page renders a small self-submitting form and the file only comes back from
    POSTing it. Rather than hardcode a body that goes stale, this replays what
    the page itself would send: every ``<input>`` in that form, by name and
    current value, posted to the form's own ``action``.

    A page usually carries several forms (search, newsletter, the download), so
    ``marker`` names an ``<input>`` unique to the one wanted and the form is
    found as that input's parent.

    Args:
        source: the source, for its shared curl_cffi session.
        url: the page carrying the form.
        marker: the ``name`` of an ``<input>`` identifying which form to submit.
        base_url: prefix for a root-relative ``action``, i.e. the scheme and
            host to put back in front of an ``/foo`` action.
        encoding: forced on the POST response before its ``.text`` is read.
            Several providers mis-declare their charset and corrupt umlauts
            otherwise. ``None`` leaves the transport's detection alone.
        headers: optional headers applied to both requests.

    Raises:
        ValueError: the page did not load, or carries no such form.
    """
    response = source.session.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(
            f"Error loading page {url}, status code {response.status_code}."
        )

    soup = BeautifulSoup(response.text, "html.parser")
    input_element = soup.find("input", {"name": marker})
    if not input_element:
        raise ValueError(f"Didn't find the input named {marker}.")
    form = input_element.find_parent("form")
    if not isinstance(form, Tag):
        raise ValueError(f"Didn't find the form around the input named {marker}.")

    form_data = {
        input_tag.get("name"): input_tag.get("value", "")
        for input_tag in form.find_all("input")
    }
    action = form.get("action")
    if not isinstance(action, str):
        raise ValueError("Didn't find the form action URL.")

    result = source.session.post(base_url + action, data=form_data, headers=headers)
    result.raise_for_status()
    if encoding is not None:
        result.encoding = encoding
    return result


class PollingIcsRetriever(_BaseRetriever):
    """GET a property page, poll an async calendar job, then fetch the ``.ics``.

    Common UK council shape: the property page kicks off server-side
    calendar generation; the client polls the ``.ics`` endpoint (the site's
    own JS does this via an htmx ``hx-trigger="every 2s"`` element) until the
    job finishes, exactly mirroring the polling the website itself performs.

    Mechanics:

    1. GET ``url`` once, to establish whatever session/cookie state the
       property page sets up server-side (some deployments key the async job
       off it).
    2. GET ``url`` + ``calendar_suffix`` repeatedly (up to ``max_attempts``
       times, sleeping ``delay`` seconds between attempts) until ``is_ready``
       returns ``True`` for a response, or attempts are exhausted.
    3. Return the last response received (ready or not; a parser's
       ``min_events`` catches a genuinely exhausted poll).

    Args:
        url: the property page URL (``callable(**source.params) -> str``, or
            a literal); also the base the calendar URL is built from.
        calendar_suffix: appended to ``url`` to build the polling endpoint
            (default ``"/calendar.ics"``).
        max_attempts: maximum polls before giving up (default 15).
        delay: seconds slept between attempts (default 2, matching the
            ``hx-trigger="every 2s"`` cadence observed on these sites).
        is_ready: ``callable(response) -> bool`` deciding whether a poll
            response is the finished calendar. Default: a ``VEVENT`` block is
            present (a real, populated ICS body rather than a pending stub).
            This is a shallow text check, not an ICS parse — parsing is still
            the parser's job.
        headers: optional headers applied to every request.
    """

    def __init__(
        self,
        *,
        url: UrlArgs,
        calendar_suffix: str = "/calendar.ics",
        max_attempts: int = 15,
        delay: float = 2,
        is_ready: Callable[[Response], bool] | None = None,
        headers: HeadersArgs = None,
    ):
        self.url = url
        self.calendar_suffix = calendar_suffix
        self.max_attempts = max_attempts
        self.delay = delay
        self.is_ready = is_ready or (lambda response: "BEGIN:VEVENT" in response.text)
        self.headers = headers

    def __call__(self, source: BaseSource) -> Response:
        headers = self._resolve(self.headers, source)
        base_url = self._resolve(self.url, source)
        calendar_url = f"{base_url}{self.calendar_suffix}"

        # Establishes any session state the property page's async job keys off.
        source.session.get(base_url, headers=headers)

        # Attempt 1 of max_attempts (no leading sleep).
        response = source.session.get(calendar_url, headers=headers)
        for _ in range(self.max_attempts - 1):
            if self.is_ready(response):
                return response
            time.sleep(self.delay)
            response = source.session.get(calendar_url, headers=headers)
        return response


class LegacyHttpGetRetriever(HttpGetRetriever):
    """HTTP GET using plain requests. Explicit non-preferred fallback.

    Only use this if curl_cffi causes a specific, documented problem with this
    source. Prefer HttpGetRetriever (curl_cffi) in all other cases.
    """

    def __call__(self, source: BaseSource) -> _plain_requests.Response:
        return _plain_requests.get(
            self._resolve(self.url, source),
            params=self._resolve(self.params, source),
            headers=_plain_headers(self._resolve(self.headers, source)),
            timeout=self.timeout,
        )


class LegacySslHttpGetRetriever(LegacyHttpGetRetriever):
    """HTTP GET using a legacy SSL session.

    Use only for endpoints that require UNSAFE_LEGACY_RENEGOTIATION (SSL
    compatibility mode).
    """

    def __call__(self, source: BaseSource) -> _plain_requests.Response:
        from waste_collection_schedule.service.SSLError import get_legacy_session

        return get_legacy_session().get(
            self._resolve(self.url, source),
            params=self._resolve(self.params, source),
            headers=_plain_headers(self._resolve(self.headers, source)),
            timeout=self.timeout,
        )


class LegacyHttpPostRetriever(HttpPostRetriever):
    """HTTP POST using plain requests. Explicit non-preferred fallback.

    Only use this if curl_cffi causes a specific, documented problem with this
    source. Prefer HttpPostRetriever (curl_cffi) in all other cases.
    """

    def __call__(self, source: BaseSource) -> _plain_requests.Response:
        return _plain_requests.post(
            self._resolve(self.url, source),
            params=self._resolve(self.params, source),
            data=self._resolve(self.data, source),
            json=self._resolve(self.json, source),
            headers=_plain_headers(self._resolve(self.headers, source)),
            timeout=self.timeout,
        )


class _DefaultHttpGetRetriever(RetrieverFunc):
    """Zero-config GET that reads request settings from the source instance.

    Reads ``API_URL``, ``_params``, ``_headers`` and ``TIMEOUT`` from the
    source so that sources which only declare ``API_URL`` keep working without
    declaring a retriever explicitly.
    """

    def __call__(self, source: BaseSource) -> Response:
        return source.session.get(
            source.API_URL,
            params=getattr(source, "_params", None),
            headers=getattr(source, "_headers", None),
            timeout=getattr(source, "TIMEOUT", 30),
        )


class _DefaultHttpPostRetriever(RetrieverFunc):
    """Zero-config POST that reads request settings from the source instance.

    Reads ``API_URL``, ``_params``, ``_data``, ``_json``, ``_headers`` and
    ``TIMEOUT`` from the source.
    """

    def __call__(self, source: BaseSource) -> Response:
        return source.session.post(
            source.API_URL,
            params=getattr(source, "_params", None),
            data=getattr(source, "_data", None),
            json=getattr(source, "_json", None),
            headers=getattr(source, "_headers", None),
            timeout=getattr(source, "TIMEOUT", 30),
        )


# Zero-config default instances (used by BaseSource and simple sources).
http_get = _DefaultHttpGetRetriever()
http_post = _DefaultHttpPostRetriever()
