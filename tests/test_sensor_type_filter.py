"""Sensor include/exclude type filters (#6908)."""

import calendar  # noqa: F401 - import stdlib calendar before the package path
import sys
from datetime import date, time, timedelta
from pathlib import Path

import pytest
import voluptuous as vol

sys.path.append(
    str(Path(__file__).parents[1] / "custom_components/waste_collection_schedule")
)
sys.path.append(str(Path(__file__).parents[1]))

from waste_collection_schedule import Collection
from waste_collection_schedule.collection_aggregator import CollectionAggregator
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    display_name,
    set_display_language,
)

from custom_components.waste_collection_schedule.const import (
    CONF_COLLECTION_TYPES,
    CONF_EXCLUDE_TYPES,
)
from custom_components.waste_collection_schedule.init_yaml import SENSOR_CONFIG
from custom_components.waste_collection_schedule.sensor import (
    DetailsFormat,
    ScheduleSensor,
)

GENERAL = display_name(GENERAL_WASTE)
BIO = display_name(ORGANIC)
PAP = display_name(PAPER)

TODAY = date.today()


class _Shell:
    """The part of a SourceShell the aggregator reads."""

    def __init__(self, entries):
        self._entries = entries
        self.refreshtime = None


@pytest.fixture(autouse=True)
def _english():
    set_display_language("en")
    yield
    set_display_language("en")


def _aggregator(*waste_types):
    return CollectionAggregator(
        [
            _Shell(
                [
                    Collection(date=TODAY + timedelta(days=i + 1), waste_type=w)
                    for i, w in enumerate(waste_types)
                ]
            )
        ]
    )


def _types(entries):
    return [e.waste_type.id for e in entries]


def test_exclude_drops_only_the_named_types():
    agg = _aggregator(GENERAL_WASTE, ORGANIC, PAPER)

    got = agg.get_upcoming(exclude_types=[GENERAL, PAP])

    assert _types(got) == ["organic"]


def test_exclude_keeps_a_type_the_source_adds_later():
    agg = _aggregator(GENERAL_WASTE, ORGANIC)
    assert _types(agg.get_upcoming(exclude_types=[GENERAL])) == ["organic"]

    later = _aggregator(GENERAL_WASTE, ORGANIC, PAPER)
    assert _types(later.get_upcoming(exclude_types=[GENERAL])) == [
        "organic",
        "paper",
    ]


def test_include_and_exclude_combine_include_first():
    agg = _aggregator(GENERAL_WASTE, ORGANIC, PAPER)

    got = agg.get_upcoming(include_types=[BIO, PAP], exclude_types=[PAP])

    assert _types(got) == ["organic"]


def test_filter_matches_the_canonical_id_and_survives_a_language_change():
    agg = _aggregator(GENERAL_WASTE, ORGANIC)

    # The id is the same in every language.
    assert _types(agg.get_upcoming(exclude_types=["general_waste"])) == ["organic"]
    assert _types(agg.get_upcoming(include_types=["organic"])) == ["organic"]

    # A name saved in English stops matching once the display language changes,
    # so the id is what keeps an exclude list from letting the type through.
    set_display_language("de")
    assert _types(agg.get_upcoming(exclude_types=["general_waste"])) == ["organic"]
    assert _types(agg.get_upcoming(exclude_types=["Restmüll"])) == ["organic"]


def test_group_by_day_honours_exclude():
    agg = _aggregator(GENERAL_WASTE, ORGANIC)

    groups = agg.get_upcoming_group_by_day(exclude_types=[GENERAL])

    assert [g.types for g in groups] == [[BIO]]


def test_no_filter_returns_everything():
    agg = _aggregator(GENERAL_WASTE, ORGANIC)

    assert len(agg.get_upcoming()) == 2
    assert len(agg.get_upcoming(exclude_types=[])) == 2


def _sensor(aggregator, details_format, types=None, exclude=None):
    class Coordinator:
        separator = ", "
        day_switch_time = time(23, 59)

    sensor = object.__new__(ScheduleSensor)
    sensor._aggregator = aggregator
    sensor._api = None
    sensor._coordinator = Coordinator()
    sensor._collection_types = types
    sensor._exclude_types = exclude
    sensor._event_index = 0
    sensor._value_template = None
    sensor._date_template = None
    sensor._add_days_to = False
    sensor._count = None
    sensor._leadtime = None
    sensor._details_format = details_format
    sensor._update_sensor()
    return sensor


def test_sensor_state_skips_an_excluded_next_collection():
    agg = _aggregator(GENERAL_WASTE, ORGANIC)

    sensor = _sensor(agg, DetailsFormat.hidden, exclude=[GENERAL])

    assert sensor._attr_extra_state_attributes["next_types"] == [BIO]


def test_appointment_types_lists_all_types_but_the_excluded_ones():
    agg = _aggregator(GENERAL_WASTE, ORGANIC, PAPER)

    sensor = _sensor(agg, DetailsFormat.appointment_types, exclude=[PAP])

    assert set(sensor._attr_extra_state_attributes) >= {GENERAL, BIO}
    assert PAP not in sensor._attr_extra_state_attributes


def test_generic_types_attribute_leaves_out_the_excluded_types():
    agg = _aggregator(GENERAL_WASTE, ORGANIC, PAPER)

    everything_but = _sensor(agg, DetailsFormat.generic, exclude=[PAP])
    assert sorted(everything_but._attr_extra_state_attributes["types"]) == [
        GENERAL,
        BIO,
    ]

    combined = _sensor(
        agg,
        DetailsFormat.generic,
        types=[BIO, PAP],
        exclude=[PAP],
    )
    assert combined._attr_extra_state_attributes["types"] == [BIO]


def test_sensor_without_exclude_is_unchanged():
    agg = _aggregator(GENERAL_WASTE, ORGANIC)

    sensor = _sensor(agg, DetailsFormat.hidden, types=[BIO])

    assert sensor._attr_extra_state_attributes["next_types"] == [BIO]


def test_yaml_sensor_accepts_exclude_types_as_scalar_or_list():
    base = {"name": "Sensor"}

    assert SENSOR_CONFIG({**base, CONF_EXCLUDE_TYPES: PAP})[CONF_EXCLUDE_TYPES] == [PAP]
    both = SENSOR_CONFIG(
        {**base, CONF_COLLECTION_TYPES: ["A"], CONF_EXCLUDE_TYPES: ["B", "C"]}
    )
    assert both[CONF_COLLECTION_TYPES] == ["A"]
    assert both[CONF_EXCLUDE_TYPES] == ["B", "C"]
    assert CONF_EXCLUDE_TYPES not in SENSOR_CONFIG(base)


def test_yaml_sensor_still_rejects_unknown_keys():
    with pytest.raises(vol.Invalid):
        SENSOR_CONFIG({"name": "Sensor", "exclude": [PAP]})
