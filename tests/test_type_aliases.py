import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "waste_collection_schedule",
        )
    ),
)

from waste_collection_schedule.collection import Collection  # noqa: E402
from waste_collection_schedule.collection_aggregator import CollectionAggregator  # noqa: E402
from waste_collection_schedule.source_shell import Customize  # noqa: E402
from waste_collection_schedule.type_aliases import (  # noqa: E402
    get_customize_label,
    get_uncustomized_types,
)


class DummyShell:
    def __init__(self, entries, customize):
        self._entries = entries
        self._customize = customize
        self.refreshtime = None


def test_aggregator_matches_aliased_entries_with_raw_filter_type():
    raw_type = "BIO (bags not required)"
    alias = "Bio"
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    shell = DummyShell(
        entries=[Collection(tomorrow, alias)],
        customize={raw_type: Customize(raw_type, alias=alias)},
    )

    aggregator = CollectionAggregator([shell])

    upcoming = aggregator.get_upcoming(include_types=[raw_type])

    assert len(upcoming) == 1
    assert upcoming[0].type == alias


def test_aggregator_groups_same_day_entries_for_combined_sensor():
    pickup_date = datetime.date.today() + datetime.timedelta(days=10)
    shell = DummyShell(
        entries=[
            Collection(pickup_date, "Bio"),
            Collection(pickup_date, "Śmieci"),
            Collection(pickup_date + datetime.timedelta(days=2), "Segregowane"),
        ],
        customize={},
    )

    aggregator = CollectionAggregator([shell])

    upcoming = aggregator.get_upcoming_group_by_day(
        count=1,
        include_types=None,
        include_today=True,
    )

    assert len(upcoming) == 1
    assert upcoming[0].types == ["Bio", "Śmieci"]


def test_uncustomized_types_do_not_repeat_aliases_of_existing_customizations():
    customize = {
        "BIO (bags not required)": {"alias": "Bio"},
        "Mixed Waste": {},
    }

    live_types = ["Bio", "Mixed Waste", "Paper"]

    assert get_uncustomized_types(live_types, customize) == ["Paper"]


def test_customize_label_prefers_alias_but_keeps_original_context():
    label = get_customize_label(
        "BIO (bags not required)",
        {"alias": "Bio"},
    )

    assert label == "Bio (BIO (bags not required))"
