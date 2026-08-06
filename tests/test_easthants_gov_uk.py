import os
import sys
from datetime import date
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

from waste_collection_schedule.source import easthants_gov_uk


def test_colour_mapping():
    assert easthants_gov_uk._normal_colour((0.248, 0.646, 0.209)) == "green"
    assert easthants_gov_uk._normal_colour((0.391, 0.389, 0.387)) == "grey"
    assert easthants_gov_uk._normal_colour((0.971, 0.66, 0.0)) == "bank_holiday"


@patch.object(easthants_gov_uk, "_parse_garden_calendar")
@patch.object(easthants_gov_uk, "_parse_bin_calendar")
@patch.object(easthants_gov_uk, "_calendar_urls")
def test_fetch_uses_selected_property_calendars(urls, parse_bins, parse_garden):
    session = Mock()
    session.get.side_effect = [
        Mock(text="selected address", content=b"address"),
        Mock(content=b"bin pdf"),
        Mock(content=b"garden pdf"),
    ]
    urls.return_value = {
        "bins": "https://example.test/bins.pdf",
        "garden": "https://example.test/garden.pdf",
    }
    parse_bins.return_value = [
        easthants_gov_uk.Collection(date=date.today(), t="Rubbish")
    ]
    parse_garden.return_value = [
        easthants_gov_uk.Collection(date=date.today(), t="Garden Waste")
    ]

    with patch.object(easthants_gov_uk.requests, "Session", return_value=session):
        collections = easthants_gov_uk.Source(1710041123).fetch()

    assert {collection.type for collection in collections} == {
        "Rubbish",
        "Garden Waste",
    }
    assert session.get.call_args_list[0].kwargs["params"] == {
        "action": "SetAddress",
        "UniqueId": "1710041123",
    }
