"""Standard retrieval methods for waste collection sources.

Each retriever is a function that takes a source instance and returns
a raw HTTP response. The source configures URL, params, headers etc
as instance/class attributes.

Preferred retrievers (curl_cffi, browser impersonation — works on Cloudflare-protected
sites and regular sites alike):

    retrieve = retrievers.http_get    # GET  — default in BaseSource
    retrieve = retrievers.http_post   # POST

Explicit fallback (plain requests — only use if curl_cffi causes a specific problem):

    retrieve = retrievers.legacy_http_get
    retrieve = retrievers.legacy_http_post
"""

import requests as _plain_requests
from curl_cffi import requests as _cffi_requests


def http_get(self) -> _cffi_requests.Response:
    """HTTP GET using curl_cffi (browser impersonation). Default retriever.

    Works on both regular endpoints and Cloudflare-protected sites.
    Reads API_URL, _params, _headers, TIMEOUT from the source instance.
    """
    session = _cffi_requests.Session(impersonate="chrome")
    return session.get(
        self.API_URL,
        params=getattr(self, "_params", None),
        headers=getattr(self, "_headers", None),
        timeout=getattr(self, "TIMEOUT", 30),
    )


def http_post(self) -> _cffi_requests.Response:
    """HTTP POST using curl_cffi (browser impersonation). Default POST retriever.

    Works on both regular endpoints and Cloudflare-protected sites.
    Reads API_URL, _params, _data, _json, _headers, TIMEOUT from the source instance.
    """
    session = _cffi_requests.Session(impersonate="chrome")
    return session.post(
        self.API_URL,
        params=getattr(self, "_params", None),
        data=getattr(self, "_data", None),
        json=getattr(self, "_json", None),
        headers=getattr(self, "_headers", None),
        timeout=getattr(self, "TIMEOUT", 30),
    )


def legacy_http_get(self) -> _plain_requests.Response:
    """HTTP GET using plain requests. Explicit non-preferred fallback.

    Only use this if curl_cffi causes a specific, documented problem with
    this source. Prefer http_get (curl_cffi) in all other cases.

    Reads API_URL, _params, _headers, TIMEOUT from the source instance.
    """
    return _plain_requests.get(
        self.API_URL,
        params=getattr(self, "_params", None),
        headers=getattr(self, "_headers", None),
        timeout=getattr(self, "TIMEOUT", 30),
    )


def legacy_ssl_http_get(self) -> _plain_requests.Response:
    """HTTP GET using a legacy SSL session. Use only for endpoints that require
    UNSAFE_LEGACY_RENEGOTIATION (SSL compatibility mode).

    Reads API_URL, _params, _headers, TIMEOUT from the source instance.
    """
    from waste_collection_schedule.service.SSLError import get_legacy_session

    return get_legacy_session().get(
        self.API_URL,
        params=getattr(self, "_params", None),
        headers=getattr(self, "_headers", None),
        timeout=getattr(self, "TIMEOUT", 30),
    )


def legacy_http_post(self) -> _plain_requests.Response:
    """HTTP POST using plain requests. Explicit non-preferred fallback.

    Only use this if curl_cffi causes a specific, documented problem with
    this source. Prefer http_post (curl_cffi) in all other cases.

    Reads API_URL, _params, _data, _json, _headers, TIMEOUT from the source instance.
    """
    return _plain_requests.post(
        self.API_URL,
        params=getattr(self, "_params", None),
        data=getattr(self, "_data", None),
        json=getattr(self, "_json", None),
        headers=getattr(self, "_headers", None),
        timeout=getattr(self, "TIMEOUT", 30),
    )
