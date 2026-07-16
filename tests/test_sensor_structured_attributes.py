import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import custom_components.waste_collection_schedule.sensor as sensor_module
from custom_components.waste_collection_schedule.sensor import (
    DetailsFormat,
    render_sensor_preview,
)
from custom_components.waste_collection_schedule.waste_collection_schedule.collection import (
    Collection,
)
from custom_components.waste_collection_schedule.waste_collection_schedule.collection_aggregator import (
    CollectionAggregator,
)


class DummyShell:
    def __init__(self, entries):
        self._entries = entries
        self._customize = {}
        self.refreshtime = None


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

    assert state == "Bio today"


def test_render_sensor_preview_exposes_grouped_pickup_attributes():
    pickup_date = datetime.date.today() + datetime.timedelta(days=10)
    aggregator = CollectionAggregator(
        [
            DummyShell(
                [
                    Collection(pickup_date, "Bio", icon="mdi:leaf"),
                    Collection(pickup_date, "Śmieci", icon="mdi:trash-can"),
                    Collection(
                        pickup_date + datetime.timedelta(days=2),
                        "Segregowane",
                        icon="mdi:recycle",
                    ),
                ]
            )
        ]
    )

    state, attributes, icon, picture = render_sensor_preview(
        aggregator=aggregator,
        separator=", ",
        day_switch_time=datetime.time(23, 59),
        details_format=DetailsFormat.upcoming,
        count=2,
        leadtime=None,
        collection_types=None,
        value_template=None,
        date_template=None,
        add_days_to=False,
        event_index=0,
    )

    assert state == "Bio, Śmieci in 10 days"
    assert icon == "mdi:numeric-2-box-multiple"
    assert picture is None
    assert attributes["next_pickup"] == {
        "date": pickup_date.isoformat(),
        "daysTo": 10,
        "types": ["Bio", "Śmieci"],
        "type": "Bio, Śmieci",
        "icon": "mdi:numeric-2-box-multiple",
        "picture": None,
    }
    assert attributes["upcoming_pickups"][0]["types"] == ["Bio", "Śmieci"]
    assert attributes["upcoming_pickups"][1]["types"] == ["Segregowane"]


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
    assert attributes["next_pickup"]["types"] == ["Bio"]


def test_render_sensor_preview_respects_hidden_details_for_structured_attributes():
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

    assert "next_pickup" not in attributes
    assert "upcoming_pickups" not in attributes


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
        "upcoming_pickups": [],
        "types": ["Bio"],
        "upcoming": [],
        "last_update": "",
    }
    assert type_attributes == {"upcoming_pickups": [], "Bio": ""}


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
