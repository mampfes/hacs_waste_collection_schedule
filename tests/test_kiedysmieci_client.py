"""Envelope handling for the kiedysmieci.info proxy client.

The proxy answers two query types through one endpoint and reports failures
inside an ``{"ok": ..., "data": ...}`` envelope rather than by status alone,
which is why ``request()`` parses the body before looking at the status. These
cover what the user is told when that envelope says no.
"""

from __future__ import annotations

from typing import Any

import pytest
import requests

from custom_components.waste_collection_schedule.waste_collection_schedule.service.KiedySmieci import (
    KiedySmieciError,
    request,
)


class FakeResponse:
    def __init__(self, status_code: int, payload: Any, is_json: bool = True) -> None:
        self.status_code = status_code
        self._payload = payload
        self._is_json = is_json

    def json(self) -> Any:
        if not self._is_json:
            raise ValueError("not json")
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Server Error")


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def get(self, _url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self.response


def _error_message(status_code: int, payload: Any) -> str:
    session = FakeSession(FakeResponse(status_code, payload))
    with pytest.raises(KiedySmieciError) as excinfo:
        request("terms", {}, session)
    return str(excinfo.value)


def test_a_failed_envelope_reports_the_provider_message() -> None:
    # A 200 carrying ok:false is the provider refusing, not failing. There is no
    # status worth repeating, so the message stands alone.
    assert _error_message(200, {"ok": False, "message": "Nieznany adres"}) == (
        "Nieznany adres"
    )


def test_a_failed_envelope_keeps_the_status_when_there_is_one() -> None:
    # The two carry different information - what went wrong, and whether the
    # provider failed or refused - so neither replaces the other.
    assert _error_message(503, {"ok": False, "message": "Service unavailable"}) == (
        "Service unavailable (HTTP 503)"
    )


def test_a_failed_envelope_without_a_message_still_names_the_status() -> None:
    # This is the case that used to report neither: a bare "unexpected response"
    # for what was really a 503.
    assert _error_message(503, {"ok": False}) == "HTTP 503"


def test_a_failed_envelope_with_nothing_to_report_says_so() -> None:
    # No message and a 200: there is genuinely nothing to name.
    assert _error_message(200, {"ok": False}) == (
        "Unexpected response from kiedysmieci.info"
    )


def test_a_non_json_body_is_left_to_the_http_client() -> None:
    # An error page rather than an envelope: raise_for_status already names the
    # status, and inventing an envelope error around it would bury that.
    session = FakeSession(FakeResponse(503, None, is_json=False))

    with pytest.raises(requests.HTTPError, match="503"):
        request("terms", {}, session)


def test_a_successful_envelope_returns_its_data() -> None:
    session = FakeSession(FakeResponse(200, {"ok": True, "data": {"listaGmin": []}}))

    assert request("locations", {"wojewodztwo": "podkarpackie"}, session) == {
        "listaGmin": []
    }
    assert session.calls[0]["params"] == {
        "type": "locations",
        "wojewodztwo": "podkarpackie",
    }
