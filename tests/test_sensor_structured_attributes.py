import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import custom_components.waste_collection_schedule.sensor as sensor_module
from custom_components.waste_collection_schedule.sensor import (
    DetailsFormat,
    render_sensor_preview,
)
from custom_components.waste_collection_schedule.waste_collection_schedule import (
    Collection,
)
from custom_components.waste_collection_schedule.waste_collection_schedule.collection_aggregator import (
    CollectionAggregator,
)
from custom_components.waste_collection_schedule.waste_collection_schedule.waste_types import (
    ORGANIC,
    set_display_language,
)


class DummyShell:
    def __init__(self, entries):
        self._entries = entries
        self._customize = {}
        self.refreshtime = None


def test_collection_aggregator_filters_by_stable_type_id_across_languages():
    pickup_date = datetime.date.today() + datetime.timedelta(days=3)
    aggregator = CollectionAggregator(
        [DummyShell([Collection(pickup_date, waste_type=ORGANIC)])]
    )

    try:
        set_display_language("de")
        assert aggregator.type_options == {"organic": "Biomüll"}
        assert aggregator.get_upcoming(include_types=["organic"])
        assert aggregator.get_upcoming(include_types=["Organic Waste"])
        assert aggregator.get_upcoming(include_types=[" BIO "])
        assert not aggregator.get_upcoming(exclude_types=["bio"])
    finally:
        set_display_language("en")


def test_collection_aggregator_keeps_direct_legacy_type_matches():
    pickup_date = datetime.date.today() + datetime.timedelta(days=3)
    aggregator = CollectionAggregator([DummyShell([Collection(pickup_date, "Bio")])])

    assert aggregator.get_upcoming(include_types=[" bio "])


def test_render_sensor_preview_uses_home_assistant_local_time(monkeypatch):
    pickup_date = datetime.date.today()
    aggregator = CollectionAggregator([DummyShell([Collection(pickup_date, "Bio")])])

    class LateSystemDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.combine(pickup_date, datetime.time(22), tz)

    monkeypatch.setattr(sensor_module.datetime, "datetime", LateSystemDateTime)
    monkeypatch.setattr(
        sensor_module.dt_util,
        "now",
        lambda: datetime.datetime.combine(pickup_date, datetime.time(8)),
    )

    state, _, _, _ = render_sensor_preview(
        aggregator=aggregator,
        separator=", ",
        day_switch_time=datetime.time(9),
        details_format=DetailsFormat.upcoming,
        count=None,
        leadtime=None,
        collection_types=None,
        value_template=None,
        date_template=None,
        add_days_to=False,
        event_index=0,
    )

    assert state == "Bio in 0 days"


def test_render_sensor_preview_defaults_missing_details_format_to_upcoming():
    pickup_date = datetime.date.today() + datetime.timedelta(days=3)
    aggregator = CollectionAggregator(
        [DummyShell([Collection(pickup_date, "Bio", icon="mdi:leaf")])]
    )

    _, attributes, _, _ = render_sensor_preview(
        aggregator=aggregator,
        separator=", ",
        day_switch_time=datetime.time(23, 59),
        details_format=None,
        count=None,
        leadtime=None,
        collection_types=None,
        value_template=None,
        date_template=None,
        add_days_to=False,
        event_index=0,
    )

    assert attributes[pickup_date.isoformat()] == "Bio"


def test_render_sensor_preview_respects_hidden_details():
    pickup_date = datetime.date.today() + datetime.timedelta(days=1)
    aggregator = CollectionAggregator(
        [DummyShell([Collection(pickup_date, "Bio", icon="mdi:leaf")])]
    )

    _, attributes, _, _ = render_sensor_preview(
        aggregator=aggregator,
        separator=", ",
        day_switch_time=datetime.time(23, 59),
        details_format=DetailsFormat.hidden,
        count=None,
        leadtime=None,
        collection_types=None,
        value_template=None,
        date_template=None,
        add_days_to=False,
        event_index=0,
    )

    assert attributes == {}


def test_render_sensor_preview_preserves_empty_pickup_detail_contracts():
    aggregator = CollectionAggregator([DummyShell([])])
    common = {
        "aggregator": aggregator,
        "separator": ", ",
        "day_switch_time": datetime.time(23, 59),
        "count": None,
        "leadtime": None,
        "collection_types": ["Bio"],
        "value_template": None,
        "date_template": None,
        "add_days_to": True,
        "event_index": 0,
    }

    state, generic_attributes, icon, picture = render_sensor_preview(
        **common,
        details_format=DetailsFormat.generic,
    )
    _, type_attributes, _, _ = render_sensor_preview(
        **common,
        details_format=DetailsFormat.appointment_types,
    )

    assert state is None
    assert icon == "mdi:trash-can"
    assert picture is None
    assert generic_attributes == {
        "types": ["Bio"],
        "upcoming": [],
        "last_update": "",
    }
    assert type_attributes == {"Bio": ""}


def test_render_sensor_preview_localizes_default_state_text():
    pickup_date = datetime.date.today() + datetime.timedelta(days=1)
    aggregator = CollectionAggregator(
        [DummyShell([Collection(pickup_date, "Bio", icon="mdi:leaf")])]
    )

    state, _, _, _ = render_sensor_preview(
        aggregator=aggregator,
        separator=", ",
        day_switch_time=datetime.time(23, 59),
        details_format=DetailsFormat.upcoming,
        count=None,
        leadtime=None,
        collection_types=None,
        value_template=None,
        date_template=None,
        add_days_to=False,
        event_index=0,
        preset_language="pl",
    )

    assert state == "Bio jutro"
