"""Prove a cassette actually pins what a source sends (#7102).

Not a test. A pytest plugin, run by hand, that adds one junk field to every
outgoing request during replay. Every request the suite makes is then wrong, so
every cassette that pins its requests must fail::

    python -m pytest tests/test_offline_fixtures.py -q -p no:cacheprovider \\
        -p tests.mutate_requests

A test that still passes under this is a test that checked nothing about what
was sent. That is how #7102 was demonstrated rather than argued: on cassettes
recorded before request bodies were stored, 679 of 682 replays passed with
every single request deliberately altered.

Cassettes recorded since do fail here, which is the point. The count of
survivors is therefore the same debt figure ``FALLBACK_BUDGET`` tracks, seen
from the other side, and it should fall as fixtures are re-recorded.
"""

from __future__ import annotations

import contextlib
import os
import sys
from typing import Any

import curl_cffi.requests as _cffi
import requests.sessions as _requests_sessions

sys.path.insert(0, os.path.dirname(__file__))

import cassette

JUNK_KEY = "__mutation_probe__"
JUNK_VALUE = "1"

_original_replaying = cassette.replaying


def _mutate_kwargs(kwargs: dict) -> None:
    """Add the junk field to whichever payload slot the request already uses."""
    for slot in ("json", "data", "params"):
        value = kwargs.get(slot)
        if isinstance(value, dict):
            kwargs[slot] = {**value, JUNK_KEY: JUNK_VALUE}
            return
        if isinstance(value, str):
            joiner = "&" if value else ""
            kwargs[slot] = f"{value}{joiner}{JUNK_KEY}={JUNK_VALUE}"
            return
        if isinstance(value, list):
            kwargs[slot] = [*value, (JUNK_KEY, JUNK_VALUE)]
            return
    # Nothing structured to alter: give it a query parameter it did not have.
    kwargs["params"] = {JUNK_KEY: JUNK_VALUE}


def _mutate_prepared(request: Any) -> None:
    body = getattr(request, "body", None)
    suffix = f"{JUNK_KEY}={JUNK_VALUE}"
    if isinstance(body, bytes):
        request.body = body + b"&" + suffix.encode()
    elif isinstance(body, str):
        request.body = f"{body}&{suffix}"
    else:
        request.body = suffix


@contextlib.contextmanager
def _mutating(path: str):
    """``cassette.replaying``, with every outgoing request altered."""
    with _original_replaying(path):
        # replaying() has just installed its lookup wrappers; wrap those, so the
        # mutation happens on the way in and the cassette sees the wrong request.
        inner_cffi = _cffi.Session.request
        inner_request = _requests_sessions.Session.request
        inner_send = _requests_sessions.Session.send

        def cffi_wrapper(self, method, url, *args, **kwargs):
            _mutate_kwargs(kwargs)
            return inner_cffi(self, method, url, *args, **kwargs)

        def request_wrapper(self, method, url, *args, **kwargs):
            _mutate_kwargs(kwargs)
            return inner_request(self, method, url, *args, **kwargs)

        def send_wrapper(self, request, **kwargs):
            _mutate_prepared(request)
            return inner_send(self, request, **kwargs)

        _cffi.Session.request = cffi_wrapper  # type: ignore[method-assign]
        _requests_sessions.Session.request = request_wrapper  # type: ignore[method-assign]
        _requests_sessions.Session.send = send_wrapper  # type: ignore[method-assign]
        try:
            yield
        finally:
            _cffi.Session.request = inner_cffi  # type: ignore[method-assign]
            _requests_sessions.Session.request = inner_request  # type: ignore[method-assign]
            _requests_sessions.Session.send = inner_send  # type: ignore[method-assign]


def pytest_configure(config) -> None:
    cassette.replaying = _mutating


def pytest_unconfigure(config) -> None:
    cassette.replaying = _original_replaying
