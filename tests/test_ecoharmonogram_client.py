from __future__ import annotations

from typing import Any

import pytest

from custom_components.waste_collection_schedule.waste_collection_schedule.service.EcoHarmonogramPL import (
    EcoharmonogramClient,
)


class FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content
        self.headers = {"content-type": "text/html; charset=UTF-8"}
        self.status_code = 200

    def raise_for_status(self) -> None:
        pass


class FakeSession:
    def __init__(self, *responses: FakeResponse) -> None:
        self.responses = iter(responses)
        self.calls: list[dict[str, Any]] = []

    def post(self, _url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return next(self.responses)


def test_client_decodes_utf8_bom_prefixed_json() -> None:
    session = FakeSession(FakeResponse(b'\xef\xbb\xbf{"towns": []}'))
    client = EcoharmonogramClient(session)

    assert client.fetch_town("Test") == {"towns": []}
    assert len(session.calls) == 1


def test_client_retries_bom_only_response_once() -> None:
    session = FakeSession(
        FakeResponse(b"\xef\xbb\xbf"),
        FakeResponse(b'\xef\xbb\xbf{"towns": []}'),
    )
    client = EcoharmonogramClient(session)

    assert client.fetch_town("Test") == {"towns": []}
    assert len(session.calls) == 2


def test_client_reports_invalid_response_shape_without_exposing_body() -> None:
    session = FakeSession(
        FakeResponse(b"\xef\xbb\xbf"),
        FakeResponse(b"<html>maintenance</html>"),
    )
    client = EcoharmonogramClient(session)

    with pytest.raises(
        ValueError,
        match=(
            "Ecoharmonogram returned invalid JSON for getTowns after 2 attempts "
            r"\(status 200, content type text/html; charset=UTF-8, 24 bytes\)"
        ),
    ):
        client.fetch_town("Test")

    assert len(session.calls) == 2
