import os
import sys
from datetime import date

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_components/waste_collection_schedule")),
)

from waste_collection_schedule.source import localwasteservices_com as lws  # noqa: E402


class FakeResponse:
    def __init__(self, text="", content=b"", status_code=200):
        self.text = text
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def get(self, url, *args, **kwargs):
        self.requests.append(("GET", url, kwargs))
        return self._responses.pop(0)

    def post(self, url, *args, **kwargs):
        self.requests.append(("POST", url, kwargs))
        return self._responses.pop(0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


DIRECTORY_HTML = """
<html>
  <body>
    <a href="/service-guidelines/city-of-gahanna---monday">City of Gahanna - Monday</a>
    <a href="/service-guidelines/city-of-hilliard">City of Hilliard</a>
    <a href="/service-guidelines/violet-township">Violet Township</a>
  </body>
</html>
"""

SERVICE_HTML = """
<html>
  <body>
    <h2>City of Gahanna - Monday</h2>
    <p>Collection Day</p>
    <p>Monday</p>
    <p>Materials out by</p>
    <p>7:00AM</p>
    <h3>Holiday Schedule</h3>
    <table>
      <tr><td>New Year’s Day</td><td>Thursday - 01/01/26</td><td>Friday - 01/01/27</td></tr>
      <tr><td>Memorial Day</td><td>Monday - 05/25/26</td><td>Monday - 05/31/27</td></tr>
      <tr><td>Christmas Day</td><td>Friday - 12/25/26</td><td>Saturday - 12/25/27</td></tr>
    </table>
    <h3>Recycling</h3>
    <p>Recyclable materials are collected weekly</p>
  </body>
</html>
"""

PDF_TEXT = """
2026 Violet Township Bi-weekly Recycling Schedule
Refugee Road and North of Refugee Road Collection Days
1/3 (Sat), 1/16, 1/30, 2/13
South of Refugee Road Collection Days
1/9, 1/23, 2/6, 2/20
"""


def test_resolve_directory_page_picks_matching_service_guidelines_url():
    url = lws._resolve_service_url_from_directory(
        DIRECTORY_HTML, "City of Hilliard", "https://localwasteservices.com/services/residential-services"
    )

    assert url == "https://localwasteservices.com/service-guidelines/city-of-hilliard"


def test_parse_service_page_extracts_weekly_trash_and_recycling_metadata():
    parsed = lws._parse_service_page(
        SERVICE_HTML,
        "https://localwasteservices.com/service-guidelines/city-of-gahanna---monday",
    )

    assert parsed["collection_day"] == "Monday"
    assert parsed["materials_out_by"] == "7:00AM"
    assert parsed["recycling_mode"] == "weekly"
    assert parsed["recycling_pdf_url"] is None
    assert date(2026, 1, 1) in parsed["holiday_dates"]
    assert date(2026, 5, 25) in parsed["holiday_dates"]
    assert date(2026, 12, 25) in parsed["holiday_dates"]


def test_parse_biweekly_pdf_text_returns_sectioned_date_lists():
    parsed = lws._parse_biweekly_pdf_text(PDF_TEXT, default_year=2026)

    assert set(parsed) == {
        "Refugee Road and North of Refugee Road Collection Days",
        "South of Refugee Road Collection Days",
    }
    assert parsed["Refugee Road and North of Refugee Road Collection Days"][0] == date(2026, 1, 3)
    assert parsed["South of Refugee Road Collection Days"][0] == date(2026, 1, 9)


def test_fetch_combines_weekly_trash_and_recycling_dates(monkeypatch):
    service_page = """
    <html>
      <body>
        <p>Collection Day</p><p>Friday</p>
        <p>Materials out by</p><p>6:00AM</p>
        <h3>Holiday Schedule</h3>
        <p>Memorial Day</p><p>Monday - 05/25/26</p>
        <p>Recycling</p><p>All recyclable materials are collected weekly</p>
      </body>
    </html>
    """

    fake_session = FakeSession([FakeResponse(text=service_page)])

    monkeypatch.setattr(lws.requests, "Session", lambda: fake_session)
    monkeypatch.setattr(
        lws,
        "_build_weekly_pickup_dates",
        lambda *args, **kwargs: [date(2026, 1, 2), date(2026, 1, 9)],
    )

    source = lws.Source(url="https://localwasteservices.com/service-guidelines/city-of-gahanna---monday")
    entries = source.fetch()

    assert [entry.type for entry in entries] == ["Trash", "Recycling", "Trash", "Recycling"]
    assert [entry.date for entry in entries] == [date(2026, 1, 2), date(2026, 1, 2), date(2026, 1, 9), date(2026, 1, 9)]
