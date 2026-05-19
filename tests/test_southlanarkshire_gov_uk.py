import os
import sys
from datetime import date
from unittest.mock import Mock, patch

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

from waste_collection_schedule.exceptions import (  # noqa: E402
    SourceArgumentNotFound,
    SourceArgumentRequired,
)
from waste_collection_schedule.source import southlanarkshire_gov_uk  # noqa: E402

SAMPLE_HTML = """
<html><body>
  <div class="bin-dir-snip">
    <p>Monday 5 January 2026 to Friday 9 January 2026</p>
    <ul>
      <li><h4>Black bin</h4></li>
    </ul>
  </div>
  <table>
    <tr><th>Black/Green - Non Recyclable Waste</th><td>Friday (Fortnightly)</td></tr>
    <tr><th>Burgundy - Food and garden</th><td>Friday (Fortnightly)</td></tr>
    <tr><th>Blue (paper and card)</th><td>Friday (4 Weekly)</td></tr>
    <tr><th>Light Grey - Glass, cans and plastics</th><td>Friday (4 Weekly)</td></tr>
  </table>
</body></html>
"""


class MockResponse:
    def __init__(self, text="", content=b"PDF", status_code=200):
        self.text = text
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        return None


@pytest.fixture
def source():
    return southlanarkshire_gov_uk.Source(
        record_id="574605",
        street_name="clincarthill_road_rutherglen",
        pdf_url="https://www.southlanarkshire.gov.uk/downloads/file/18302/hamilton_and_clydesdale_bin_collection_calendar_2026_-_households_with_food_and_garden_waste_collected_on_the_same_week_as_general_waste",
    )


def test_init_requires_pdf_url():
    with pytest.raises(SourceArgumentRequired):
        southlanarkshire_gov_uk.Source(
            record_id="574605",
            street_name="clincarthill_road_rutherglen",
            pdf_url="",
        )


def test_to_download_pdf_url_normalizes_listing_link(source):
    listing_url = (
        "https://www.southlanarkshire.gov.uk/downloads/file/18302/"
        "hamilton_and_clydesdale_bin_collection_calendar_2026_-_households_with_"
        "food_and_garden_waste_collected_on_the_same_week_as_general_waste"
    )

    resolved = source._to_download_pdf_url(listing_url)

    assert resolved == (
        "https://www.southlanarkshire.gov.uk/download/downloads/id/18302/"
        "hamilton_and_clydesdale_bin_collection_calendar_2026_-_households_with_"
        "food_and_garden_waste_collected_on_the_same_week_as_general_waste.pdf"
    )


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
def test_resolve_pdf_url_prefers_matching_variant(mock_session, source):
    html = """
    <html><body>
      <a href="https://www.southlanarkshire.gov.uk/downloads/file/18301/east_kilbride_cambuslang_and_rutherglen_bin_collection_calendar_2026">A</a>
      <a href="https://www.southlanarkshire.gov.uk/downloads/file/18300/hamilton_and_clydesdale_bin_collection_calendar_2026">B</a>
      <a href="https://www.southlanarkshire.gov.uk/downloads/file/18302/hamilton_and_clydesdale_bin_collection_calendar_2026_-_households_with_food_and_garden_waste_collected_on_the_same_week_as_general_waste">C</a>
    </body></html>
    """
    session = Mock()
    session.get.return_value = MockResponse(text=html)
    mock_session.return_value = session

    resolved = source._resolve_pdf_url(Mock())

    assert "/18302/" in resolved
    assert resolved.endswith(".pdf")


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.PdfReader")
def test_parse_pdf_schedule_extracts_labels_and_dates(
    mock_pdf_reader, mock_session, source
):
    session = Mock()
    session.get.return_value = MockResponse(content=b"PDF")
    mock_session.return_value = session

    page = Mock()
    page.extract_text.return_value = """
    Black/Green - Non Recyclable Waste
    5 January
    Light Grey - Glass, cans and plastics
    Burgundy - Food and garden
    12 January
    filler
    filler
    filler
    filler
    Blue (paper and card)
    Burgundy - Food and garden
    26 January
    """
    mock_pdf_reader.return_value.pages = [page]

    schedule = source._parse_pdf_schedule("https://example.com/calendar_2026.pdf")

    assert schedule[date(2026, 1, 5)] == "black"
    assert schedule[date(2026, 1, 12)] == "grey+burgundy"
    assert schedule[date(2026, 1, 26)] == "blue+burgundy"
    assert source._label_for_color("black") == "Black/Green - Non Recyclable Waste"
    assert source._label_for_color("grey") == "Light Grey - Glass, cans and plastics"


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.PdfReader")
def test_parse_pdf_schedule_uses_date_only_fallback(
    mock_pdf_reader, mock_session, source
):
    session = Mock()
    session.get.return_value = MockResponse(content=b"PDF")
    mock_session.return_value = session

    page = Mock()
    page.extract_text.return_value = "5 January 12 January 19 January 26 January"
    mock_pdf_reader.return_value.pages = [page]

    schedule = source._parse_pdf_schedule("https://example.com/calendar_2026.pdf")

    assert schedule[date(2026, 1, 5)] == "black"
    assert schedule[date(2026, 1, 12)] == "grey+burgundy"
    assert schedule[date(2026, 1, 19)] == "black"
    assert schedule[date(2026, 1, 26)] == "blue+burgundy"


@patch.object(
    southlanarkshire_gov_uk.Source, "_determine_cycle_position", return_value=0
)
@patch.object(
    southlanarkshire_gov_uk.Source,
    "_parse_pdf_schedule",
    return_value={date(2026, 1, 12): "grey+burgundy"},
)
@patch.object(
    southlanarkshire_gov_uk.Source,
    "_resolve_pdf_url",
    return_value="https://example.com/calendar_2026.pdf",
)
@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
def test_fetch_returns_labels_from_table_rows(
    mock_session,
    _resolve_pdf_url,
    _parse_pdf_schedule,
    _determine_cycle_position,
    source,
):
    session = Mock()
    session.get.return_value = MockResponse(text=SAMPLE_HTML)
    mock_session.return_value = session

    entries = source.fetch()

    first_day = [entry for entry in entries if entry.date == date(2026, 1, 9)]
    assert [entry.type for entry in first_day] == ["Black/Green - Non Recyclable Waste"]
    assert first_day[0].icon == "mdi:trash-can"

    second_cycle_day = [entry for entry in entries if entry.date == date(2026, 1, 16)]
    assert [entry.type for entry in second_cycle_day] == [
        "Light Grey - Glass, cans and plastics",
        "Burgundy - Food and garden",
    ]


@patch("waste_collection_schedule.source.southlanarkshire_gov_uk.requests.Session")
def test_fetch_raises_for_missing_bin_info(mock_session, source):
    session = Mock()
    session.get.return_value = MockResponse(
        text="<html><body>No bin info</body></html>"
    )
    mock_session.return_value = session

    with pytest.raises(SourceArgumentNotFound):
        source.fetch()
