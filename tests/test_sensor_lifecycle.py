"""Sensor migrations and lifecycle edits against real Home Assistant registries."""

import asyncio
import inspect
import sys
from datetime import date
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

import pytest
import pytest_asyncio
from homeassistant import loader
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity, frame, translation
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.append(
    str(Path(__file__).parents[1] / "custom_components/waste_collection_schedule")
)

from waste_collection_schedule import Collection
from waste_collection_schedule.source_shell import SourceShell
from waste_collection_schedule.waste_types import GLASS, PAPER

from custom_components.waste_collection_schedule.const import DOMAIN
from custom_components.waste_collection_schedule.default_sensors import (
    LEGACY_VALUE_TEMPLATE,
    catalogue,
)
from custom_components.waste_collection_schedule.init_ui import async_migrate_entry
from custom_components.waste_collection_schedule.sensor_model import SensorConfig


@pytest_asyncio.fixture
async def ha(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    hass.config_entries = ConfigEntries(hass, {})
    hass.config.skip_pip = True
    loader.async_setup(hass)
    if hasattr(entity, "async_setup"):
        entity.async_setup(hass)
    if hasattr(translation, "async_setup"):
        translation.async_setup(hass)
    if hasattr(frame, "async_setup"):
        frame.async_setup(hass)
    await hass.config_entries.async_initialize()
    if hasattr(dr, "async_setup"):
        dr.async_setup(hass)
    await asyncio.gather(dr.async_load(hass), er.async_load(hass), ir.async_load(hass))
    yield hass
    await hass.async_stop(force=True)


def entry_for(hass, options, *, version=4):
    # Constructor metadata differs across the supported HA runtimes; the
    # persisted entry contract under test is the same.
    kwargs = {
        "domain": DOMAIN,
        "title": "My collection",
        "data": {"name": "ecoharmonogram_pl", "args": {}},
        "options": options,
        "source": "user",
        "unique_id": "fixture",
        "version": version,
        "minor_version": 0,
        "discovery_keys": MappingProxyType({}),
        "subentries_data": [],
    }
    kwargs = {
        k: v
        for k, v in kwargs.items()
        if k in inspect.signature(ConfigEntry).parameters
    }
    entry = ConfigEntry(**kwargs)
    hass.config_entries._entries[entry.entry_id] = entry
    return entry


@pytest.mark.asyncio
async def test_v3_migration_preserves_registry_identity_disabled_state_and_orphans(ha):
    options = {
        "sensors": [
            {
                "name": "My blue bin",
                "types": [PAPER.names["en"]],
                "value_template": LEGACY_VALUE_TEMPLATE,
                "details_format": "upcoming",
            },
            {
                "name": "Just my provider bin",
                "types": ["Small paper bin"],
                "value_template": "{{ value.daysTo + 2 }}",
            },
        ]
    }
    entry = entry_for(ha, options, version=3)
    registry = er.async_get(ha)
    old = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        entry.entry_id + "_ui_sensor_My blue bin",
        suggested_object_id="my_blue_bin",
        config_entry=entry,
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    orphan = registry.async_get_or_create(
        "sensor", DOMAIN, entry.entry_id + "_ui_sensor_Old name", config_entry=entry
    )
    assert await async_migrate_entry(ha, entry)
    assert entry.version == 4
    assert (
        registry.async_get(old.entity_id).unique_id
        == entry.entry_id + "_sensor_type_paper"
    )
    assert (
        registry.async_get(old.entity_id).disabled_by == er.RegistryEntryDisabler.USER
    )
    assert entry.options["sensors"][0]["enabled"] is False
    assert entry.options["sensors"][1]["types"] == ["Small paper bin"]
    assert registry.async_get(orphan.entity_id) is not None
    assert (
        ir.async_get(ha).async_get_issue(DOMAIN, "legacy_sensors_" + entry.entry_id)
        is not None
    )
    migrated = list(entry.options["sensors"])
    assert await async_migrate_entry(ha, entry)
    assert entry.options["sensors"] == migrated


@pytest.mark.asyncio
async def test_v2_registry_migrates_source_and_sensor_identity_in_one_pass(ha):
    from custom_components.waste_collection_schedule.init_ui import (
        _get_source_unique_id,
    )

    entry = entry_for(
        ha,
        {
            "sensors": [
                {
                    "name": "Paper",
                    "types": [PAPER.names["en"]],
                    "value_template": LEGACY_VALUE_TEMPLATE,
                }
            ]
        },
        version=2,
    )
    registry = er.async_get(ha)
    old = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        _get_source_unique_id(entry.data) + "_ui_sensor_Paper",
        config_entry=entry,
    )
    assert await async_migrate_entry(ha, entry)
    assert (
        registry.async_get(old.entity_id).unique_id
        == entry.entry_id + "_sensor_type_paper"
    )
    assert entry.version == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("frozen", [False, True])
async def test_published_device_preview_sensor_identity_is_migrated(ha, frozen):
    old = {
        "name": "Renamed preview sensor",
        "sensor_id": "previewid",
        "types": ["Small paper bin"],
    }
    if frozen:
        old["sensor_legacy_unique_id"] = "old_source_ui_sensor_Original name"
    entry = entry_for(ha, {"sensors": [old]}, version=3)
    suffix = "Original name" if frozen else "previewid"
    registry = er.async_get(ha)
    registered = registry.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_ui_sensor_{suffix}", config_entry=entry
    )
    assert await async_migrate_entry(ha, entry)
    record = entry.options["sensors"][0]
    assert (
        registry.async_get(registered.entity_id).unique_id
        == f"{entry.entry_id}_sensor_{record['id']}"
    )
    assert record["types"] == ["Small paper bin"]


@pytest.mark.asyncio
async def test_future_entry_version_is_rejected_without_changing_data(ha):
    entry = entry_for(ha, {"sensors": [{"future": "record"}]}, version=5)
    assert not await async_migrate_entry(ha, entry)
    assert entry.version == 5
    assert entry.options["sensors"] == [{"future": "record"}]


class FixtureSource:
    def __init__(self):
        self.fetch_count = 0
        self.types = [PAPER]

    def fetch(self):
        self.fetch_count += 1
        return [Collection(date=date(2099, 1, 1), waste_type=t) for t in self.types]


@pytest_asyncio.fixture
async def running_entry(ha, tmp_path):
    components = tmp_path / "custom_components"
    components.mkdir()
    (components / DOMAIN).symlink_to(
        Path(__file__).parents[1] / "custom_components" / DOMAIN,
        target_is_directory=True,
    )
    source = FixtureSource()
    shell = SourceShell(
        source=source,
        customize={},
        title="Synthetic provider",
        description="Offline fixture",
        url=None,
        calendar_title="My bins",
        unique_id="fixture",
        day_offset=0,
    )
    records = list(catalogue({"paper": "Paper"}).values())
    records.append(SensorConfig(name="Custom paper", types=["paper"]).as_dict())
    entry = entry_for(
        ha, {"sensors": records, "device_controls": False, "auto_add_types": False}
    )
    with patch(
        "custom_components.waste_collection_schedule.init_ui.SourceShell.create",
        return_value=shell,
    ):
        assert await ha.config_entries.async_setup(entry.entry_id)
        await ha.async_block_till_done()
        yield entry, source
        await ha.config_entries.async_unload(entry.entry_id)
        await ha.async_block_till_done()


@pytest.mark.asyncio
async def test_manager_edits_keep_entity_id_and_do_not_fetch(running_entry, ha):
    entry, source = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    record = entry.options["sensors"][0]
    registry = er.async_get(ha)
    entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, entry.entry_id + "_sensor_" + record["id"]
    )
    assert ha.states.get(entity_id) is not None
    assert source.fetch_count == 1
    await manager.async_update(
        record["id"],
        {"name": "Renamed paper", "state_format": "days", "color": "#123456"},
    )
    await ha.async_block_till_done()
    assert (
        registry.async_get_entity_id(
            "sensor", DOMAIN, entry.entry_id + "_sensor_" + record["id"]
        )
        == entity_id
    )
    assert registry.async_get(entity_id).original_name == "Renamed paper"
    assert ha.states.get(entity_id).attributes["color"] == "#123456"
    assert source.fetch_count == 1


@pytest.mark.asyncio
async def test_manager_disable_mirrors_registry_and_delete_removes_custom_identity(
    running_entry, ha
):
    entry, source = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    registry = er.async_get(ha)
    custom = next(r for r in entry.options["sensors"] if r["origin"] == "custom")
    uid = entry.entry_id + "_sensor_" + custom["id"]
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, uid)
    await manager.async_set_enabled(custom["id"], False)
    await ha.async_block_till_done()
    assert registry.async_get(entity_id).disabled_by is not None
    assert ha.states.get(entity_id) is None
    registry.async_update_entity(entity_id, disabled_by=None)
    await ha.async_block_till_done()
    assert (
        next(r for r in entry.options["sensors"] if r["id"] == custom["id"])["enabled"]
        is True
    )
    assert await ha.config_entries.async_reload(entry.entry_id)
    await ha.async_block_till_done()
    assert registry.async_get_entity_id("sensor", DOMAIN, uid) == entity_id
    assert ha.states.get(entity_id) is not None
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    await manager.async_delete(custom["id"])
    await ha.async_block_till_done()
    assert registry.async_get(entity_id) is None
    assert source.fetch_count == 1


@pytest.mark.asyncio
async def test_options_and_native_controls_edit_the_same_saved_record(
    running_entry, ha
):
    from custom_components.waste_collection_schedule.sensor_options import (
        SensorOptionsFlow,
    )

    entry, source = running_entry
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    selected = [
        r["origin"] for r in entry.options["sensors"] if r["origin"] != "custom"
    ]
    form = await flow.async_step_sensors(
        {"predefined": selected, "edit_sensor": "add_custom", "device_controls": True}
    )
    assert form["step_id"] == "edit_sensor"
    result = await flow.async_step_edit_sensor(
        {
            "name": "My second paper sensor",
            "types": ["paper"],
            "state_format": "relative",
            "language": "en",
            "date_format": "dmy",
            "details_format": "generic",
            "kind": "schedule",
            "enabled": True,
        }
    )
    ha.config_entries.async_update_entry(entry, options=result["data"])
    await ha.async_block_till_done()
    record = next(
        r for r in entry.options["sensors"] if r["name"] == "My second paper sensor"
    )
    registry = er.async_get(ha)
    select_id = registry.async_get_entity_id(
        "select", DOMAIN, f"{entry.entry_id}_control_{record['id']}_state_format"
    )
    assert ha.states.get(select_id) is not None
    await ha.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_id, "option": "days"},
        blocking=True,
    )
    await ha.async_block_till_done()
    updated = next(r for r in entry.options["sensors"] if r["id"] == record["id"])
    assert updated["state_format"] == "days"
    sensor_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_sensor_{record['id']}"
    )
    assert ha.states.get(sensor_id).state.isdigit()
    assert source.fetch_count == 1
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    await manager.async_update(record["id"], {"kind": "last_update"})
    await ha.async_block_till_done()
    assert (
        registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_sensor_{record['id']}"
        )
        == sensor_id
    )
    assert ha.states.get(sensor_id).attributes["device_class"] == "timestamp"
    assert (
        registry.async_get_entity_id(
            "select", DOMAIN, f"{entry.entry_id}_control_{record['id']}_state_format"
        )
        is None
    )
    await manager.async_update(record["id"], {"kind": "schedule"})
    await ha.async_block_till_done()
    assert ha.states.get(select_id) is not None
    await manager.async_delete(record["id"])
    await ha.async_block_till_done()
    assert registry.async_get(sensor_id) is None
    assert not any(
        e.unique_id.startswith(f"{entry.entry_id}_control_{record['id']}_")
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    )
    retained = {
        e.unique_id: e.entity_id
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == "sensor"
    }
    ha.config_entries.async_update_entry(
        entry, options={**entry.options, "device_controls": False}
    )
    await ha.async_block_till_done()
    assert not any(
        e.unique_id.startswith(
            (entry.entry_id + "_control_", entry.entry_id + "_create_")
        )
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    )
    assert {
        e.unique_id: e.entity_id
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == "sensor"
    } == retained
    assert source.fetch_count == 1


@pytest.mark.asyncio
async def test_discovered_types_materialize_once_and_vanished_types_keep_identity(
    running_entry, ha
):
    entry, source = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]
    registry = er.async_get(ha)
    paper_id = registry.async_get_entity_id(
        "sensor", DOMAIN, entry.entry_id + "_sensor_type_paper"
    )
    ha.config_entries.async_update_entry(
        entry, options={**entry.options, "auto_add_types": True}
    )
    await ha.async_block_till_done()
    source.types = [PAPER, GLASS]
    coordinator._last_fetch_date = None
    await coordinator.async_refresh()
    await ha.async_block_till_done()
    assert (
        len([r for r in entry.options["sensors"] if r["origin"] == "type:glass"]) == 1
    )
    assert (
        registry.async_get_entity_id(
            "sensor", DOMAIN, entry.entry_id + "_sensor_type_paper"
        )
        == paper_id
    )
    source.types = [GLASS]
    coordinator._last_fetch_date = None
    await coordinator.async_refresh()
    await ha.async_block_till_done()
    assert (
        len([r for r in entry.options["sensors"] if r["origin"] == "type:glass"]) == 1
    )
    assert ha.states.get(paper_id).state == "unknown"
    assert any(r["origin"] == "type:paper" for r in entry.options["sensors"])


@pytest.mark.asyncio
async def test_yaml_formats_kinds_and_unique_ids_work_in_both_configuration_paths(
    ha, tmp_path
):
    from homeassistant.setup import async_setup_component

    components = tmp_path / "custom_components"
    components.mkdir()
    (components / DOMAIN).symlink_to(
        Path(__file__).parents[1] / "custom_components" / DOMAIN,
        target_is_directory=True,
    )
    config = {
        DOMAIN: {
            "sources": [
                {
                    "name": "static",
                    "args": {
                        "type": "Paper",
                        "frequency": "YEARLY",
                        "start": "2099-01-01",
                        "until": "2099-12-31",
                    },
                }
            ],
            "sensors": [
                {
                    "name": "German paper",
                    "unique_id": "old_paper_name",
                    "state_format": "relative",
                    "language": "de",
                    "date_format": "dmy",
                    "types": ["legacy_Paper"],
                    "exclude_types": ["glass"],
                    "unique_types": True,
                    "color": "#123456",
                    "details_format": "generic",
                    "count": 1,
                },
                {"name": "Numeric paper", "kind": "days_to"},
                {"name": "Fetched paper", "kind": "last_update"},
                {"name": "Legacy text"},
            ],
        },
        "sensor": [
            {
                "platform": DOMAIN,
                "name": "Classic paper",
                "unique_id": "classic_old_name",
                "state_format": "types",
                "unique_types": True,
            }
        ],
    }
    assert await async_setup_component(ha, DOMAIN, config)
    await ha.async_block_till_done()
    registry = er.async_get(ha)
    german_id = registry.async_get_entity_id("sensor", DOMAIN, "old_paper_name")
    german = ha.states.get(german_id)
    days = (date(2099, 1, 1) - date.today()).days
    assert german.state == f"in {days} Tagen"
    assert german.attributes["color"] == "#123456"
    assert german.attributes["upcoming"][0]["type_id"] == "legacy_Paper"
    assert german.attributes["upcoming"][0]["color"] == "#123456"
    assert ha.states.get("sensor.numeric_paper").state == str(days)
    assert (
        ha.states.get("sensor.fetched_paper").attributes["device_class"] == "timestamp"
    )
    assert ha.states.get("sensor.legacy_text").state == f"Paper in {days} days"
    classic_id = registry.async_get_entity_id("sensor", DOMAIN, "classic_old_name")
    assert ha.states.get(classic_id).state == "Paper"
