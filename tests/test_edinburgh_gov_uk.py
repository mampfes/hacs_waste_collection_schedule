import os
import sys
from datetime import date, timedelta
from unittest.mock import Mock, patch

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

from waste_collection_schedule.source import edinburgh_gov_uk


def response(text, status_code=200, json_data=None, content=None):
    result = Mock(text=text, status_code=status_code)
    result.content = content if content is not None else text.encode()
    result.json.return_value = json_data or {}
    result.raise_for_status.return_value = None
    return result


SEARCH_HTML = '<a class="list__link" href="/directory-record/1">Morningside Road</a>'
THREE_HTML = '<dl><dt>Calendar code</dt><dd><a href="/downloads/file/30262/calendar">Tue_1</a></dd></dl>'
FOOD_HTML = "<dl><dt>Collection day</dt><dd>Wednesday</dd></dl>"
GARDEN_HTML = '<dl><dt>Calendar</dt><dd><a href="/downloads/file/garden-waste-calendar-friday-2">calendar</a></dd></dl>'


@patch.object(
    edinburgh_gov_uk,
    "_parse_garden_pdf",
    return_value={date.today() + timedelta(days=3)},
)
@patch.object(
    edinburgh_gov_uk,
    "_parse_calendar_pdf",
    return_value={
        "Grey Bin": {date.today() + timedelta(days=1)},
        "Green Bin": {date.today() + timedelta(days=2)},
        "Glass Box": {date.today() + timedelta(days=2)},
    },
)
@patch.object(edinburgh_gov_uk.requests, "get")
def test_fetch_parses_all_edinburgh_streams(get, parse_calendar, parse_garden):
    get.side_effect = [
        response(SEARCH_HTML),
        response(THREE_HTML),
        response("", content=b"%PDF"),
        response(SEARCH_HTML),
        response(FOOD_HTML),
        response(SEARCH_HTML),
        response(GARDEN_HTML),
        response("", content=b"%PDF"),
    ]

    collections = edinburgh_gov_uk.Source("EH10 4AY", "1 Morningside Road").fetch()

    assert len(collections) > 0
    assert {collection.type for collection in collections} == {
        "Food Waste Bin",
        "Brown Garden Waste Bin",
        "Grey Bin",
        "Green Bin",
        "Glass Box",
    }
    assert collections == sorted(collections, key=lambda item: item.date)


def test_parse_calendar_codes():
    assert edinburgh_gov_uk._parse_code("Tue_2") == ("Tuesday", 1)
    assert edinburgh_gov_uk._parse_code("Tue_1A") == ("Tuesday", 0)
    assert edinburgh_gov_uk._parse_garden_code("friday-1") == ("Friday", 0)
    assert edinburgh_gov_uk._parse_code("bad") == (None, None)


def test_paon_is_optional():
    source = edinburgh_gov_uk.Source("EH8 7SB")

    assert source._paon is None
