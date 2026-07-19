"""Record/replay HTTP at the session layer, for offline source tests.

Both HTTP stacks the sources use (curl_cffi for retrievers, plain ``requests``
for many services) route most calls through ``Session.request``, so patching
that one method on each stack intercepts the bulk of traffic (multi-request
handshakes, any follow-up fetches a parser makes). A few services bypass it and
call ``requests`` ``Session.send`` directly with a prepared request (e.g.
``AppAbfallplusDe``); ``Session.send`` is patched too so that traffic is
captured, with a re-entrancy guard so the normal ``request -> send`` path is not
recorded twice.

* ``recording(path)`` wraps a live ``fetch()``: real requests go through, and
  each (request -> response) interaction is saved to a cassette JSON file, with
  the recording date.
* ``replaying(path)`` serves those recorded responses instead of hitting the
  network, and freezes the clock to the recording date so date-windowed sources
  (ICS feeds, recurrence projections) stay deterministic.

Cassettes are matched by method + URL (+ a body hash for POSTs), consumed in
order so repeated identical requests replay correctly.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import threading
from typing import Any

import curl_cffi.requests as _cffi
import requests
import requests.sessions as _requests_sessions
from freezegun import freeze_time


def _body_hash(kwargs: dict) -> str:
    body = kwargs.get("json")
    if body is None:
        body = kwargs.get("data")
    if body is None:
        body = kwargs.get("params")
    if body is None:
        return ""
    return hashlib.sha1(repr(body).encode("utf-8")).hexdigest()[:10]


def _key(method: str, url: str, kwargs: dict) -> str:
    return f"{method.upper()} {url} {_body_hash(kwargs)}"


class CassetteResponse:
    """Stand-in for an HTTP response, backed by a recorded interaction."""

    def __init__(self, interaction: dict):
        self.status_code: int = interaction["status"]
        self._content: bytes = base64.b64decode(interaction["content_b64"])
        self.encoding: str = interaction.get("encoding") or "utf-8"
        self.headers: dict = interaction.get("headers") or {}
        self.url: str = interaction.get("url", "")

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def text(self) -> str:
        return self._content.decode(self.encoding, errors="replace")

    @property
    def apparent_encoding(self) -> str:
        """Charset detected from the body, mirroring requests' Response."""
        try:
            from charset_normalizer import from_bytes

            best = from_bytes(self._content).best()
            if best and best.encoding:
                return best.encoding
        except Exception:
            pass
        return self.encoding or "utf-8"

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    @property
    def reason(self) -> str:
        return "" if self.ok else f"HTTP {self.status_code}"

    def json(self) -> Any:
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise OSError(f"cassette response status {self.status_code}")


def _requests_response(interaction: dict) -> requests.Response:
    """Build a genuine ``requests.Response`` from a recorded interaction.

    The ``Session.send`` path replays a real Response (not the CassetteResponse
    stand-in) because some services type-check with ``isinstance(r,
    requests.Response)`` (e.g. AppAbfallplusDe's ``extract_onclicks``).
    """
    resp = requests.Response()
    resp.status_code = interaction["status"]
    resp._content = base64.b64decode(interaction["content_b64"])
    resp.encoding = interaction.get("encoding") or "utf-8"
    resp.headers.update(interaction.get("headers") or {})
    resp.url = interaction.get("url", "")
    return resp


def _capture(resp: Any, method: str, url: str, kwargs: dict) -> dict:
    try:
        headers = dict(resp.headers)
    except Exception:
        headers = {}
    return {
        "key": _key(method, url, kwargs),
        "method": method.upper(),
        "url": url,
        "status": resp.status_code,
        "encoding": getattr(resp, "encoding", None),
        "headers": headers,
        "content_b64": base64.b64encode(resp.content).decode("ascii"),
    }


def _prepared_key(request: Any) -> str:
    """Cassette key for a requests ``PreparedRequest`` (the ``Session.send`` path).

    At send time params are already folded into ``request.url`` and the body is
    the encoded ``request.body``, so the key is built from those rather than from
    the ``request()``-level kwargs.
    """
    body = getattr(request, "body", None)
    body_hash = (
        hashlib.sha1(repr(body).encode("utf-8")).hexdigest()[:10]
        if body is not None
        else ""
    )
    return f"{request.method.upper()} {request.url} {body_hash}"


def _capture_prepared(resp: Any, request: Any) -> dict:
    try:
        headers = dict(resp.headers)
    except Exception:
        headers = {}
    return {
        "key": _prepared_key(request),
        "method": request.method.upper(),
        "url": request.url,
        "status": resp.status_code,
        "encoding": getattr(resp, "encoding", None),
        "headers": headers,
        "content_b64": base64.b64encode(resp.content).decode("ascii"),
    }


@contextlib.contextmanager
def recording(path: str, today: str, extra: dict | None = None):
    """Patch both stacks to pass through and record interactions to ``path``.

    ``extra`` is merged into the saved cassette JSON (e.g. the parent/child
    values a ``get_choices`` replay test asserts against). ``replaying`` ignores
    any keys beyond ``interactions``/``recorded_at``.
    """
    interactions: list[dict] = []
    orig_cffi_request = _cffi.Session.request
    orig_request = _requests_sessions.Session.request
    orig_send = _requests_sessions.Session.send
    # requests' Session.request calls Session.send internally, so when both are
    # patched a normal request would be captured twice. This guard marks the
    # window inside our request wrapper so the nested send passes through
    # silently; only a *direct* Session.send call (no request wrapper around it,
    # e.g. AppAbfallplusDe) records at the send layer.
    guard = threading.local()

    def request_wrapper(orig):
        def wrapper(self, method, url, *args, **kwargs):
            outer = not getattr(guard, "active", False)
            if outer:
                guard.active = True
            try:
                resp = orig(self, method, url, *args, **kwargs)
            finally:
                if outer:
                    guard.active = False
            try:
                interactions.append(_capture(resp, method, url, kwargs))
            except Exception:
                pass
            return resp

        return wrapper

    def send_wrapper(self, request, **kwargs):
        resp = orig_send(self, request, **kwargs)
        if not getattr(guard, "active", False):
            try:
                interactions.append(_capture_prepared(resp, request))
            except Exception:
                pass
        return resp

    _cffi.Session.request = request_wrapper(orig_cffi_request)  # type: ignore[method-assign]
    _requests_sessions.Session.request = request_wrapper(orig_request)  # type: ignore[method-assign]
    _requests_sessions.Session.send = send_wrapper  # type: ignore[method-assign]
    success = False
    try:
        yield interactions
        success = True
    finally:
        _cffi.Session.request = orig_cffi_request  # type: ignore[method-assign]
        _requests_sessions.Session.request = orig_request  # type: ignore[method-assign]
        _requests_sessions.Session.send = orig_send  # type: ignore[method-assign]
        # Only persist a cassette for a clean run, so a failed fetch never
        # leaves a partial/misleading recording behind.
        if success:
            payload = {"recorded_at": today, "interactions": interactions}
            if extra:
                payload.update(extra)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(payload, fh, indent=2)
                fh.write("\n")


@contextlib.contextmanager
def replaying(path: str):
    """Serve recorded responses (no network) with the clock frozen to record day."""
    with open(path, encoding="utf-8") as fh:
        cassette = json.load(fh)
    interactions = cassette["interactions"]
    used = [False] * len(interactions)

    def _find(key: str, method: str, url: str) -> dict:
        for i, it in enumerate(interactions):
            if not used[i] and it["key"] == key:
                used[i] = True
                return it
        # Fall back to method+url (body may not reproduce byte-for-byte).
        for i, it in enumerate(interactions):
            if not used[i] and it["method"] == method.upper() and it["url"] == url:
                used[i] = True
                return it
        raise AssertionError(f"no recorded interaction for {method.upper()} {url}")

    def lookup(method: str, url: str, kwargs: dict) -> CassetteResponse:
        return CassetteResponse(_find(_key(method, url, kwargs), method, url))

    def lookup_prepared(request: Any) -> requests.Response:
        return _requests_response(
            _find(_prepared_key(request), request.method, request.url)
        )

    def lookup_request_real(method: str, url: str, kwargs: dict) -> requests.Response:
        return _requests_response(_find(_key(method, url, kwargs), method, url))

    orig_cffi_request = _cffi.Session.request
    orig_request = _requests_sessions.Session.request
    orig_send = _requests_sessions.Session.send

    def cffi_request_wrapper(self, method, url, *args, **kwargs):
        return lookup(method, url, kwargs)

    def requests_request_wrapper(self, method, url, *args, **kwargs):
        # Serve the requests stack a genuine requests.Response so services that
        # type-check with isinstance(r, requests.Response) still work.
        return lookup_request_real(method, url, kwargs)

    def send_wrapper(self, request, **kwargs):
        # A request()-based call is served (and short-circuited) by the request
        # wrapper, so send is only reached by a direct Session.send call.
        return lookup_prepared(request)

    _cffi.Session.request = cffi_request_wrapper  # type: ignore[method-assign]
    _requests_sessions.Session.request = requests_request_wrapper  # type: ignore[method-assign]
    _requests_sessions.Session.send = send_wrapper  # type: ignore[method-assign]
    try:
        with freeze_time(cassette["recorded_at"]):
            yield
    finally:
        _cffi.Session.request = orig_cffi_request  # type: ignore[method-assign]
        _requests_sessions.Session.request = orig_request  # type: ignore[method-assign]
        _requests_sessions.Session.send = orig_send  # type: ignore[method-assign]
