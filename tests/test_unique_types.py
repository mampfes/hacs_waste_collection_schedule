"""Coverage for optional per-type deduplication of upcoming collections."""

import asyncio
import json
import sys
from copy import deepcopy
from datetime import date, time, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, mock_open, patch

import homeassistant  # noqa: F401 - load its Voluptuous compatibility first
import pytest
import voluptuous as vol

sys.path.append(
    str(Path(__file__).parents[1] / "custom_components/waste_collection_schedule")
)

from waste_collection_schedule import Collection, CollectionAggregator  # isort:skip


def make_aggregator():
    """Merge unsorted synthetic schedules from two sources."""
    today = date.today()
    shells = [
        SimpleNamespace(
            _entries=[
                Collection(today + timedelta(days=5), "General"),
                Collection(today + timedelta(days=2), "Paper"),
                Collection(today + timedelta(days=1), "General"),
            ],
            refreshtime=None,
        ),
        SimpleNamespace(
            _entries=[
                Collection(today + timedelta(days=4), "Glass"),
                Collection(today + timedelta(days=2), "General"),
                Collection(today + timedelta(days=3), "Paper"),
                Collection(today + timedelta(days=7), "Glass"),
            ],
            refreshtime=None,
        ),
    ]
    return CollectionAggregator(shells), shells


def test_default_retains_repeated_types():
    """Existing consumers keep every event unless they enable the option."""
    aggregator, _ = make_aggregator()
    assert [entry.type for entry in aggregator.get_upcoming(count=3)] == [
        "General",
        "Paper",
        "General",
    ]


def test_unique_types_uses_next_date_across_sources_before_count_and_index():
    """Later repeats do not crowd a less frequent type out of the result."""
    aggregator, shells = make_aggregator()
    original_entries = [list(shell._entries) for shell in shells]
    upcoming = aggregator.get_upcoming(unique_types=True, count=3)
    assert [entry.type for entry in upcoming] == ["General", "Paper", "Glass"]
    assert upcoming == sorted(upcoming, key=lambda entry: entry.date)
    assert (
        aggregator.get_upcoming(unique_types=True, start_index=1, count=2)
        == upcoming[1:]
    )
    assert [shell._entries for shell in shells] == original_entries
    assert upcoming[0] is shells[0]._entries[2]


def test_unique_types_filters_before_grouping_days():
    """Distinct types share a date, then count and index apply to dates."""
    aggregator, shells = make_aggregator()
    same_day = date.today() + timedelta(days=2)
    shells[1]._entries.append(Collection(same_day, "Food"))
    shells[1]._entries.append(Collection(same_day, "Paper"))

    groups = aggregator.get_upcoming_group_by_day(unique_types=True, count=2)
    assert [group.types for group in groups] == [["General"], ["Paper", "Food"]]
    groups = aggregator.get_upcoming_group_by_day(
        unique_types=True, start_index=1, count=2
    )
    assert [group.types for group in groups] == [["Paper", "Food"], ["Glass"]]


@pytest.mark.parametrize("include_today", [False, True])
def test_expired_entries_do_not_hide_next_collection(include_today):
    """Deduplication considers only the entries left after date filtering."""
    today = date.today()
    shell = SimpleNamespace(
        _entries=[
            Collection(today - timedelta(days=1), "Paper"),
            Collection(today, "Paper"),
            Collection(today + timedelta(days=1), "Paper"),
        ]
    )
    result = CollectionAggregator([shell]).get_upcoming(
        unique_types=True, include_today=include_today
    )
    assert len(result) == 1
    assert result[0].date == today + timedelta(days=0 if include_today else 1)


@pytest.mark.parametrize(
    ("options", "expected_types"),
    [
        ({"include_types": ["Paper", "Glass"]}, ["Paper", "Glass"]),
        ({"exclude_types": ["General"]}, ["Paper", "Glass"]),
        ({"leadtime": 3}, ["General", "Paper"]),
        ({"include_types": []}, []),
        ({"count": 0}, []),
        ({"start_index": 3}, []),
    ],
)
def test_unique_types_respects_existing_filters(options, expected_types):
    aggregator, _ = make_aggregator()
    result = aggregator.get_upcoming(unique_types=True, **options)
    assert [entry.type for entry in result] == expected_types


def test_unique_types_preserves_first_event_metadata():
    """An alias is the identity and the first same-date event wins."""
    today = date.today()
    first = Collection(
        today + timedelta(days=1),
        "My paper",
        icon="mdi:newspaper",
        picture="/local/synthetic-paper.png",
        location="Test collection point",
    )
    later = Collection(today + timedelta(days=2), "My paper")
    duplicate = Collection(today + timedelta(days=1), "My paper")
    shell = SimpleNamespace(_entries=[later, first, duplicate])
    result = CollectionAggregator([shell]).get_upcoming(unique_types=True)
    assert result == [first]
    assert result[0] is first


def test_unique_types_handles_an_empty_schedule():
    aggregator = CollectionAggregator([SimpleNamespace(_entries=[])])
    assert aggregator.get_upcoming(unique_types=True) == []
    assert aggregator.get_upcoming_group_by_day(unique_types=True) == []


@pytest.mark.parametrize("schema_kind", ["ui", "yaml", "legacy"])
@pytest.mark.parametrize("enabled", [None, False, True])
def test_unique_types_schema_parity(schema_kind, enabled):
    """UI and both YAML entry points default off and accept the same flag."""
    from custom_components.waste_collection_schedule.config_flow import (
        get_sensor_schema,
    )
    from custom_components.waste_collection_schedule.init_yaml import SENSOR_CONFIG
    from custom_components.waste_collection_schedule.sensor import PLATFORM_SCHEMA

    schema = {
        "ui": get_sensor_schema(["General", "Paper", "Glass"]),
        "yaml": SENSOR_CONFIG,
        "legacy": PLATFORM_SCHEMA,
    }[schema_kind]
    config = {"name": "Synthetic collections"}
    if schema_kind == "legacy":
        config["platform"] = "waste_collection_schedule"
    if enabled is not None:
        config["unique_types"] = enabled
    assert schema(config)["unique_types"] is (enabled or False)
    with pytest.raises(vol.Invalid):
        schema({**config, "unique_types": "not a boolean"})


@pytest.mark.parametrize("setup_kind", ["ui", "yaml", "legacy"])
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("details_format", ["upcoming", "generic", "appointment_types"])
def test_sensor_setup_applies_unique_types(setup_kind, enabled, details_format):
    """The real setup functions wire the option through to state and details."""
    from custom_components.waste_collection_schedule import sensor
    from custom_components.waste_collection_schedule.config_flow import (
        get_sensor_schema,
        validate_sensor_user_input,
    )
    from custom_components.waste_collection_schedule.init_yaml import SENSOR_CONFIG

    aggregator, _ = make_aggregator()
    shell = SimpleNamespace(
        _entries=aggregator._entries,
        refreshtime=None,
        calendar_title="Synthetic collections",
        unique_id="synthetic-source",
    )
    coordinator = SimpleNamespace(
        separator=", ", day_switch_time=time(0), device_info={}
    )
    coordinator.shell = shell
    api = SimpleNamespace(
        get_shell=lambda index: shell,
        shells=[shell],
        separator=", ",
        _day_switch_time=time(0),
    )
    hass = SimpleNamespace(
        data={sensor.DOMAIN: {"entry": coordinator, "YAML_CONFIG": api}}
    )
    config = {
        "name": "Synthetic collections",
        "details_format": details_format,
        "unique_types": enabled,
        "event_index": 1,
        "count": 3,
    }
    add_entities = Mock()

    async def run():
        if setup_kind == "ui":
            args, errors = validate_sensor_user_input(get_sensor_schema([])(config), [])
            assert not errors
            entry = SimpleNamespace(entry_id="entry", options={"sensors": [args]})
            await sensor.async_setup_entry(hass, entry, add_entities)
        elif setup_kind == "yaml":
            await sensor.async_setup_platform(
                hass,
                {},
                add_entities,
                discovery_info={"api": api, "sensor_config": SENSOR_CONFIG(config)},
            )
        else:
            await sensor.async_setup_platform(
                hass,
                sensor.PLATFORM_SCHEMA(
                    {**config, "platform": "waste_collection_schedule"}
                ),
                add_entities,
            )

    with patch.object(sensor, "async_dispatcher_connect", return_value=lambda: None):
        asyncio.run(run())
    entity = add_entities.call_args.args[0][0]
    entity._update_sensor()
    assert entity.native_value.startswith(
        "Paper in" if enabled else "Paper, General in"
    )
    attributes = entity.extra_state_attributes
    if details_format == "upcoming":
        assert list(attributes.values()) == (
            ["Paper", "Glass"] if enabled else ["Paper, General", "Paper", "Glass"]
        )
    elif details_format == "generic":
        assert [item.type for item in attributes["upcoming"]] == (
            ["General", "Paper", "Glass"]
            if enabled
            else ["General", "Paper", "General"]
        )
    else:
        today = date.today()
        assert attributes == {
            "General": (today + timedelta(days=2)).isoformat(),
            "Glass": (today + timedelta(days=7)).isoformat(),
            "Paper": (today + timedelta(days=3)).isoformat(),
        }


def test_ui_edit_schema_keeps_the_saved_setting():
    from custom_components.waste_collection_schedule.config_flow import (
        get_sensor_schema,
    )

    schema = get_sensor_schema([], add_delete=True, defaults={"unique_types": True})
    assert schema({"name": "Synthetic collections"})["unique_types"] is True


@pytest.mark.parametrize(
    ("language", "label"),
    [
        ("en", "Show each waste type once"),
        ("de", "Jede Abfallart nur einmal anzeigen"),
    ],
)
def test_generated_sensor_labels_preserve_existing_translations(language, label):
    """Test generation in memory without rewriting generated repository files."""
    from update_docu_links import add_sensor_translations

    path = (
        Path(__file__).parents[1]
        / "custom_components/waste_collection_schedule/translations"
        / f"{language}.json"
    )
    original = json.loads(path.read_text(encoding="utf-8"))
    translated = deepcopy(original)
    add_sensor_translations(translated, language)
    once = deepcopy(translated)
    add_sensor_translations(translated, language)
    assert translated == once
    for flow in ("config", "options"):
        sensor = translated[flow]["step"]["sensor"]
        assert sensor["data"].pop("unique_types") == label
        assert sensor["data_description"].pop("unique_types")
        original_sensor = original[flow]["step"]["sensor"]
        original_sensor["data"].pop("unique_types", None)
        original_sensor["data_description"].pop("unique_types", None)
    assert translated == original


@pytest.mark.parametrize("language", ["en", "de"])
def test_normal_json_generation_emits_sensor_labels(language):
    """Exercise the workflow's generator path with all file I/O mocked."""
    import update_docu_links

    translations = {
        "config": {
            "step": {
                "args": {"data": {}},
                "reconfigure": {"data": {}},
                "sensor": {"data": {}},
            }
        },
        "options": {"step": {"sensor": {"data": {}}}},
    }
    with (
        patch.object(update_docu_links, "LANGUAGES", [language]),
        patch.object(update_docu_links, "update_sources_json"),
        patch.object(
            update_docu_links, "get_custom_translations", return_value=({}, {}, {}, {})
        ),
        patch.object(update_docu_links.Path, "exists", return_value=True),
        patch.object(
            update_docu_links,
            "open",
            mock_open(read_data=json.dumps(translations)),
            create=True,
        ),
        patch.object(update_docu_links.json, "dump") as dump_json,
    ):
        update_docu_links.update_json({})

    dump_json.assert_called_once()
    output = dump_json.call_args.args[0]
    for flow in ("config", "options"):
        sensor = output[flow]["step"]["sensor"]
        assert sensor["data"]["unique_types"]
        assert sensor["data_description"]["unique_types"]
