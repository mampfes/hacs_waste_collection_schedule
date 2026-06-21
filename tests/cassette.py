"""Record/replay HTTP at the session layer, for offline source tests.

Both HTTP stacks the sources use (curl_cffi for retrievers, plain ``requests``
for many services) funnel every call through ``Session.request``, so patching
that one method on each stack intercepts all traffic — including multi-request
handshakes and any follow-up fetches a parser makes.

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
from typing import Any

import curl_cffi.requests as _cffi
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


@contextlib.contextmanager
def recording(path: str, today: str):
    """Patch both stacks to pass through and record interactions to ``path``."""
    interactions: list[dict] = []
    originals = (_cffi.Session.request, _requests_sessions.Session.request)

    def make(orig):
        def wrapper(self, method, url, *args, **kwargs):
            resp = orig(self, method, url, *args, **kwargs)
            try:
                interactions.append(_capture(resp, method, url, kwargs))
            except Exception:
                pass
            return resp

        return wrapper

    _cffi.Session.request = make(originals[0])  # type: ignore[method-assign]
    _requests_sessions.Session.request = make(originals[1])  # type: ignore[method-assign]
    success = False
    try:
        yield interactions
        success = True
    finally:
        _cffi.Session.request, _requests_sessions.Session.request = originals  # type: ignore[method-assign]
        # Only persist a cassette for a clean run, so a failed fetch never
        # leaves a partial/misleading recording behind.
        if success:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(
                    {"recorded_at": today, "interactions": interactions}, fh, indent=2
                )
                fh.write("\n")


@contextlib.contextmanager
def replaying(path: str):
    """Serve recorded responses (no network) with the clock frozen to record day."""
    with open(path, encoding="utf-8") as fh:
        cassette = json.load(fh)
    interactions = cassette["interactions"]
    used = [False] * len(interactions)

    def lookup(method: str, url: str, kwargs: dict) -> CassetteResponse:
        key = _key(method, url, kwargs)
        for i, it in enumerate(interactions):
            if not used[i] and it["key"] == key:
                used[i] = True
                return CassetteResponse(it)
        # Fall back to method+url (body may not reproduce byte-for-byte).
        for i, it in enumerate(interactions):
            if not used[i] and it["method"] == method.upper() and it["url"] == url:
                used[i] = True
                return CassetteResponse(it)
        raise AssertionError(f"no recorded interaction for {method.upper()} {url}")

    originals = (_cffi.Session.request, _requests_sessions.Session.request)

    def wrapper(self, method, url, *args, **kwargs):
        return lookup(method, url, kwargs)

    _cffi.Session.request = wrapper  # type: ignore[method-assign]
    _requests_sessions.Session.request = wrapper  # type: ignore[method-assign]
    try:
        with freeze_time(cassette["recorded_at"]):
            yield
    finally:
        _cffi.Session.request, _requests_sessions.Session.request = originals  # type: ignore[method-assign]
