import json
import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "waste_collection_schedule",
        )
    )
)

from waste_collection_schedule.exceptions import SourceArgumentNotFound  # noqa: E402
from waste_collection_schedule.source import southlanarkshire_gov_uk  # noqa: E402

_PREMISES_JSON = json.dumps(
    [{"id": 576, "UPRN": 484000578, "Premises": "11 Chapel Court, Glasgow, G73 1UR"}]
)
_APPOINTMENTS_JSON = json.dumps(
    [
        {
            "Id": 1,
            "UPRN": 484000600,
            "Subject": "Black Bin",
            "StartTime": "2026-05-04T00:00:00",
            "EndTime": "2026-05-04T00:00:00",
            "IsAllDay": True,
        },
        {
            "Id": 2,
            "UPRN": 484000600,
            "Subject": "Grey Bin",
            "StartTime": "2026-04-27T00:00:00",
            "EndTime": "2026-04-27T00:00:00",
            "IsAllDay": True,
        },
        {
            "Id": 3,
            "UPRN": 484000600,
            "Subject": "Grey Bin",
            "StartTime": "2026-04-27T00:00:00",
            "EndTime": "2026-04-27T00:00:00",
            "IsAllDay": True,
        },
    ]
)

SAMPLE_HTML = (
    "<!DOCTYPE html><html><head><title>Public Dashboard</title></head><body>"
    '<input name="__RequestVerificationToken" value="test-csrf-token" type="hidden" />'
    "<script>"
    'new ejs.dropdowns.DropDownList({"dataSource": ejs.data.DataUtil.parse.isJson('
    + _PREMISES_JSON
    + ")});"
    'new ejs.Schedule({"dataSource": ejs.data.DataUtil.parse.isJson('
    + _APPOINTMENTS_JSON
    + ")});"
    "</script></body></html>"
)


class MockResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def source():
    return southlanarkshire_gov_uk.Source(postcode="G73 1UR", uprn=484000600)


def test_init_normalises_postcode():
    s = southlanarkshire_gov_uk.Source(postcode="  g73 1ur  ", uprn=484000600)
    assert s._postcode == "G73 1UR"


def test_init_coerces_uprn_to_int():
    s = southlanarkshire_gov_uk.Source(postcode="G73 1UR", uprn="484000600")
    assert s._uprn == 484000600


def test_extract_appointments_returns_appointments_block():
    appts = southlanarkshire_gov_uk.Source._extract_appointments(SAMPLE_HTML)
    assert len(appts) == 3
    assert appts[0]["Subject"] == "Black Bin"


def test_extract_appointments_skips_premises_block():
    appts = southlanarkshire_gov_uk.Source._extract_appointments(SAMPLE_HTML)
    assert all("Subject" in a for a in appts)


def test_extract_appointments_returns_empty_list_when_not_found():
    appts = southlanarkshire_gov_uk.Source._extract_appointments(
        "<html><body>no data here</body></html>"
    )
    assert appts == []


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
def test_fetch_returns_collection_entries(mock_session_cls, source):
    session = MagicMock()
    session.get.return_value = MockResponse(text=SAMPLE_HTML)
    session.post.return_value = MockResponse(text=SAMPLE_HTML)
    mock_session_cls.return_value = session
    entries = source.fetch()
    assert len(entries) == 2
    subjects = {e.type for e in entries}
    assert subjects == {"Black Bin", "Grey Bin"}


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
def test_fetch_deduplicates_entries(mock_session_cls, source):
    session = MagicMock()
    session.get.return_value = MockResponse(text=SAMPLE_HTML)
    session.post.return_value = MockResponse(text=SAMPLE_HTML)
    mock_session_cls.return_value = session
    entries = source.fetch()
    grey_entries = [e for e in entries if e.type == "Grey Bin"]
    assert len(grey_entries) == 1


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
def test_fetch_uses_correct_date(mock_session_cls, source):
    session = MagicMock()
    session.get.return_value = MockResponse(text=SAMPLE_HTML)
    session.post.return_value = MockResponse(text=SAMPLE_HTML)
    mock_session_cls.return_value = session
    entries = source.fetch()
    black_entry = next(e for e in entries if e.type == "Black Bin")
    assert black_entry.date == date(2026, 5, 4)


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
def test_fetch_raises_when_no_appointments_found(mock_session_cls, source):
    empty_html = '<html><body><input name="__RequestVerificationToken" value="tok" /></body></html>'
    session = MagicMock()
    session.get.return_value = MockResponse(text=empty_html)
    session.post.return_value = MockResponse(text=empty_html)
    mock_session_cls.return_value = session
    with pytest.raises(SourceArgumentNotFound):
        source.fetch()


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
def test_fetch_posts_to_select_prem_handler(mock_session_cls, source):
    session = MagicMock()
    session.get.return_value = MockResponse(text=SAMPLE_HTML)
    session.post.return_value = MockResponse(text=SAMPLE_HTML)
    mock_session_cls.return_value = session
    source.fetch()
    call_kwargs = session.post.call_args
    assert call_kwargs[1]["params"] == {"handler": "SelectPrem"}
    assert call_kwargs[1]["data"]["SelectedPostcode"] == "G73 1UR"
    assert call_kwargs[1]["data"]["SelectedPremises"] == "484000600"
    assert call_kwargs[1]["data"]["__RequestVerificationToken"] == "test-csrf-token"
