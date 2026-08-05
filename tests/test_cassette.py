"""Unit tests for the record/replay harness itself (``tests/cassette.py``).

The harness is what every offline source test trusts, so the properties it has
to hold are worth asserting directly rather than inferring from 682 green
replays. The ones here are the subject of #7102:

* a recording stores the request body, on both capture paths;
* replay refuses a request whose body differs from the recorded one;
* a cassette recorded before bodies were stored replays exactly as before.

Everything runs offline: ``replaying`` patches both HTTP stacks, so the requests
these tests issue never leave the process.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import typing

import pytest
import requests

sys.path.insert(0, os.path.dirname(__file__))

import cassette

URL = "https://example.invalid/api"


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode("ascii")


def _interaction(**overrides) -> dict:
    it = {
        "key": "",
        "method": "POST",
        "url": URL,
        "final_url": URL,
        "status": 200,
        "encoding": "utf-8",
        "headers": {},
        "content_b64": base64.b64encode(b"ok").decode("ascii"),
    }
    it.update(overrides)
    return it


def _cassette(tmp_path, *interactions: dict, name: str = "case.json") -> str:
    path = os.path.join(tmp_path, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"recorded_at": "2026-01-01", "interactions": list(interactions)}, fh)
    return path


# --------------------------------------------------------------------------
# Canonical rendering
# --------------------------------------------------------------------------


def test_body_rendering_ignores_key_order():
    """The same payload in a different key order is the same request."""
    assert cassette._body({"json": {"a": 1, "b": 2}}) == cassette._body(
        {"json": {"b": 2, "a": 1}}
    )
    assert cassette._body({"data": {"a": "1", "b": "2"}}) == cassette._body(
        {"data": {"b": "2", "a": "1"}}
    )
    assert cassette._body({"params": {"z": "1", "a": "2"}}) == cassette._body(
        {"params": {"a": "2", "z": "1"}}
    )


def test_body_rendering_is_the_same_however_the_body_was_built():
    """``data=`` as a dict, as a query string and as bytes are one request.

    This is what keeps the fix from making honest refactors look like behaviour
    changes: moving a hand-built body onto ``data=`` must still match.
    """
    as_dict = cassette._body({"data": {"a": 1, "b": "x y"}})
    as_string = cassette._body({"data": "b=x+y&a=1"})
    as_bytes = cassette._body({"data": b"a=1&b=x%20y"})
    assert as_dict == as_string == as_bytes


def test_a_prepared_body_renders_like_the_request_that_produced_it():
    """The ``Session.send`` path and the ``Session.request`` path agree."""

    class _Req:
        body = b'{"b": 2, "a": 1}'

    assert cassette._prepared_body(_Req()) == cassette._body({"json": {"a": 1, "b": 2}})

    class _Form:
        body = "b=2&a=1"

    assert cassette._prepared_body(_Form()) == cassette._body(
        {"data": {"a": 1, "b": 2}}
    )


def test_body_rendering_covers_every_payload_slot():
    """``params`` beside ``json`` is in the body even though the hash misses it.

    ``_body_hash`` returns on the first of json/data/params it finds, so a
    source sending both had its params compared nowhere at all.
    """
    with_params = cassette._body({"json": {"a": 1}, "params": {"page": "2"}})
    without = cassette._body({"json": {"a": 1}, "params": {"page": "3"}})
    assert with_params != without
    assert cassette._body({"json": {"a": 1}, "params": {"page": "2"}}, False) == (
        cassette._body({"json": {"a": 1}, "params": {"page": "3"}}, False)
    )


def test_a_multipart_boundary_does_not_defeat_matching():
    """requests invents a fresh boundary per request; it must not be compared."""

    class _Req:
        body = (
            "--a1b2c3d4e5f6\r\n"
            'Content-Disposition: form-data; name="x"\r\n\r\n1\r\n'
            "--a1b2c3d4e5f6--\r\n"
        )

    class _Same:
        body = _Req.body.replace("a1b2c3d4e5f6", "999888777666")

    assert cassette._prepared_body(_Req()) == cassette._prepared_body(_Same())


def test_an_undecodable_body_still_renders_deterministically():
    class _Req:
        body = b"\xff\xfe\x00binary"

    rendered = cassette._prepared_body(_Req())
    assert "base64:" in rendered
    assert rendered == cassette._prepared_body(_Req())


# --------------------------------------------------------------------------
# Recording
# --------------------------------------------------------------------------


def test_a_capture_always_stores_a_body_field():
    """Empty string included, so an absent field means "recorded before this"."""

    class _Resp:
        status_code = 200
        encoding = "utf-8"
        headers: typing.ClassVar[dict] = {}
        content = b"ok"
        url = URL

    posted = cassette._capture(_Resp(), "post", URL, {"json": {"a": 1}})
    assert json.loads(posted["body"]) == {"body": {"a": 1}}

    plain = cassette._capture(_Resp(), "get", URL, {})
    assert plain["body"] == ""


# --------------------------------------------------------------------------
# Replay
# --------------------------------------------------------------------------


def test_a_matching_body_replays(tmp_path):
    body = cassette._body({"json": {"a": 1}})
    path = _cassette(tmp_path, _interaction(key="k", body=body))
    with cassette.replaying(path):
        resp = requests.Session().request("POST", URL, json={"a": 1})
    assert resp.content == b"ok"


def test_a_changed_body_fails_and_prints_both_sides(tmp_path):
    """The whole point of #7102: a changed body must not replay green."""
    path = _cassette(
        tmp_path, _interaction(key="k", body=cassette._body({"json": {"a": 1}}))
    )
    with pytest.raises(AssertionError) as excinfo:
        with cassette.replaying(path):
            requests.Session().request("POST", URL, json={"a": 2})
    message = str(excinfo.value)
    assert "recorded" in message and "sent" in message
    assert '"a":1' in message and '"a":2' in message


def test_a_changed_get_param_fails(tmp_path):
    """Not only POSTs: the params on a GET were never compared either."""
    path = _cassette(
        tmp_path,
        _interaction(
            key="k", method="GET", body=cassette._body({"params": {"id": "1"}})
        ),
    )
    with pytest.raises(AssertionError):
        with cassette.replaying(path):
            requests.Session().request("GET", URL, params={"id": "2"})


def test_a_cassette_with_no_body_field_replays_as_before(tmp_path):
    """Additive: the 682 cassettes recorded before this keep working untouched."""
    path = _cassette(tmp_path, _interaction(key="mismatched-on-purpose"))
    with cassette.replaying(path):
        resp = requests.Session().request("POST", URL, json={"anything": "at all"})
    assert resp.content == b"ok"


def test_positional_pairing_of_same_url_posts_is_stopped(tmp_path):
    """Two POSTs to one URL were paired by position, not by what was sent.

    The fallback takes the first *unused* interaction with a matching
    method+url, so a body change did not merely fail to be noticed: it could
    hand a request the response recorded for a different one.
    """
    first = cassette._body({"data": {"step": "1"}})
    second = cassette._body({"data": {"step": "2"}})
    path = _cassette(
        tmp_path,
        _interaction(key="a", body=first, content_b64=_b64("one")),
        _interaction(key="b", body=second, content_b64=_b64("two")),
    )
    # Asked for step 2 first, the old matcher handed back step 1's response.
    with cassette.replaying(path):
        resp = requests.Session().request("POST", URL, data={"step": "2"})
    assert resp.content == b"two"


def test_the_fallback_count_is_recorded(tmp_path):
    """The budget gate reads this; an exact-key hit must not be counted."""
    path = _cassette(tmp_path, _interaction(key="not-the-key-we-will-send"))
    with cassette.replaying(path):
        requests.Session().request("POST", URL, json={"a": 1})
    assert cassette.REPLAY_FALLBACKS[os.path.abspath(path)] == 1

    exact = cassette._key("POST", URL, {"json": {"a": 1}})
    path2 = _cassette(tmp_path, _interaction(key=exact), name="exact.json")
    with cassette.replaying(path2):
        requests.Session().request("POST", URL, json={"a": 1})
    assert cassette.REPLAY_FALLBACKS[os.path.abspath(path2)] == 0
