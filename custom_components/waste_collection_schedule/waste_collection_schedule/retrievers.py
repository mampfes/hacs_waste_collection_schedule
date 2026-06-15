"""Standard retrieval methods for waste collection sources.

Each retriever is a typed callable that takes a source instance and returns a
raw HTTP response. A retriever is configured either declaratively (passing the
URL/params/headers to its constructor, optionally as callables resolved against
``source.params``) or implicitly via the zero-config default instances, which
read ``API_URL`` / ``_params`` / ``_headers`` etc. from the source.

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

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Mapping, Protocol, TypeAlias, cast

import requests as _plain_requests
from curl_cffi import requests as _cffi_requests

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

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
    """A callable that fetches a raw HTTP response for a source."""

    def __call__(self, source: BaseSource) -> Response: ...

    def _resolve[T](self, mapping: Callable[..., T] | T, source: BaseSource) -> T:
        """Resolve a constructor argument against the source's params.

        If ``mapping`` is callable, call it with ``**source.params`` so a
        source's user-supplied arguments flow into the URL/params/headers.
        Otherwise return the literal value.
        """
        if callable(mapping):
            return mapping(**source.params)
        return cast("T", mapping)


class HttpGetRetriever(RetrieverFunc):
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
        session = _cffi_requests.Session(impersonate="chrome")
        return session.get(
            self._resolve(self.url, source),
            params=self._resolve(self.params, source),
            headers=self._resolve(self.headers, source),
            timeout=self.timeout,
        )


class HttpPostRetriever(RetrieverFunc):
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
        session = _cffi_requests.Session(impersonate="chrome")
        return session.post(
            self._resolve(self.url, source),
            params=self._resolve(self.params, source),
            data=self._resolve(self.data, source),
            json=self._resolve(self.json, source),
            headers=self._resolve(self.headers, source),
            timeout=self.timeout,
        )


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
        session = _cffi_requests.Session(impersonate="chrome")
        return session.get(
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
        session = _cffi_requests.Session(impersonate="chrome")
        return session.post(
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
