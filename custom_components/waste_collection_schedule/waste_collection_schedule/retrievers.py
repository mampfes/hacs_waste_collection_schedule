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

import time
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, TypeVar, cast

import requests as _plain_requests
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from curl_cffi import requests as _cffi_requests

    from waste_collection_schedule.base_source import BaseSource

T = TypeVar("T")

Response: TypeAlias = "_plain_requests.Response | _cffi_requests.Response"

HeadersType: TypeAlias = Mapping[str, str | None] | None
ParamsType: TypeAlias = dict | list | tuple | None
JsonType: TypeAlias = dict | list | None

SourceParams: TypeAlias = dict[str, Any]
UrlArgs: TypeAlias = Callable[..., str] | str
ParamsArgs: TypeAlias = Callable[..., ParamsType] | ParamsType
HeadersArgs: TypeAlias = Callable[..., HeadersType] | HeadersType
AnyArgs: TypeAlias = Callable[..., Any] | Any
JsonArgs: TypeAlias = Callable[..., JsonType] | JsonType


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
#
# Not a TypedDict: `submit_action` is required while `fields`/`remove` are
# not, and PEP 655 Required/NotRequired needs a newer typing than this
# module's pyright target -- a plain dict keeps step access unchecked but
# simple; see AthosWasteManagementRetriever's docstring for the worked shape.
AthosStep: TypeAlias = "dict[str, Any]"


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
            fields[name] = tag.get("value", "")
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
       form state (the wizard's server-side session key/values).
    3. For each entry in ``steps`` (in order): merge ``fields(**source.params)``
       into the running state, drop any ``remove`` keys, set
       ``SubmitAction`` to ``submit_action`` (resolved against
       ``source.params`` if callable), then POST the accumulated state back to
       the servlet URL.
    4. Return the *last* step's response (the ICS download) unparsed; pair
       with ``parsers.IcsParser()`` / ``parsers.IcsEventsParser()``.

    The form state accumulates across steps (a later step inherits every
    earlier step's fields unless a step's ``remove`` drops them) because the
    servlet is itself stateless between POSTs — the growing form *is* the
    session.

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
    ):
        if not steps:
            raise ValueError("AthosWasteManagementRetriever requires at least one step")
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

    def _apply_encoding(self, response: Response) -> Response:
        if self.encoding is not None:
            response.encoding = self.encoding
        return response

    def __call__(self, source: BaseSource) -> Response:
        headers = self._resolve(self.headers, source)
        url = self._resolve(self.url, source)

        initial = source.session.get(url, params=self.initial_params, headers=headers)
        if initial.status_code == 404 and self.fallback_url is not None:
            url = self._resolve(self.fallback_url, source)
            initial = source.session.get(
                url, params=self.initial_params, headers=headers
            )
        initial.raise_for_status()
        self._apply_encoding(initial)

        state: dict[str, Any] = _scrape_hidden_inputs(initial.text)

        response = initial
        for step in self.steps:
            state.update(step["fields"](**source.params) if "fields" in step else {})
            for key in step.get("remove", ()):
                state.pop(key, None)
            state["SubmitAction"] = self._resolve(step["submit_action"], source)
            # A fresh copy per POST: state is mutated further by later steps,
            # and callers (session mocks in tests, request logging, retry
            # wrappers) may hold onto the `data` they were given rather than
            # consuming it immediately.
            response = source.session.post(url, data=dict(state), headers=headers)
            response.raise_for_status()
            self._apply_encoding(response)

        return response


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
            headers=self._resolve(self.headers, source),
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
            headers=self._resolve(self.headers, source),
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
            headers=self._resolve(self.headers, source),
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
