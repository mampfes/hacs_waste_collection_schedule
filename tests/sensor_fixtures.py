"""Shared real-Home-Assistant fixtures for sensor lifecycle and acceptance."""

import asyncio
import inspect
import sys
from datetime import date
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

import pytest_asyncio
from homeassistant import auth, loader
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity, frame, restore_state, translation
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.append(
    str(Path(__file__).parents[1] / "custom_components/waste_collection_schedule")
)

from waste_collection_schedule import Collection
from waste_collection_schedule.source_shell import Customize, SourceShell
from waste_collection_schedule.waste_types import PAPER

from custom_components.waste_collection_schedule.const import DOMAIN
from custom_components.waste_collection_schedule.default_sensors import (
    catalogue,
)
from custom_components.waste_collection_schedule.sensor_model import SensorConfig


@pytest_asyncio.fixture
async def ha(tmp_path, monkeypatch):
    from waste_collection_schedule.service import DeviceKeyStore

    from custom_components.waste_collection_schedule.waste_collection_schedule.service import (
        DeviceKeyStore as IntegrationDeviceKeyStore,
    )

    monkeypatch.setattr(DeviceKeyStore, "_device_key_store", None)
    monkeypatch.setattr(IntegrationDeviceKeyStore, "_device_key_store", None)
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
    await asyncio.gather(
        dr.async_load(hass),
        er.async_load(hass),
        ir.async_load(hass),
        restore_state.async_load(hass),
    )
    hass.auth = await auth.auth_manager_from_config(
        hass, [{"type": "homeassistant"}], []
    )
    yield hass
    await hass.async_block_till_done()
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


class FixtureSource:
    def __init__(self):
        self.fetch_count = 0
        self.types = [PAPER]

    def fetch(self):
        self.fetch_count += 1
        return [Collection(date=date(2099, 1, 1), waste_type=t) for t in self.types]


@pytest_asyncio.fixture
async def running_entry(ha, tmp_path, request):
    components = tmp_path / "custom_components"
    components.mkdir()
    (components / DOMAIN).symlink_to(
        Path(__file__).parents[1] / "custom_components" / DOMAIN,
        target_is_directory=True,
    )
    source = FixtureSource()
    initial = getattr(request, "param", {})
    source.types = initial.get("types", [PAPER])
    shell = SourceShell(
        source=source,
        customize={
            key: Customize(waste_type=key, **value)
            for key, value in initial.get("options", {}).get("customize", {}).items()
        },
        title="Synthetic provider",
        description="Offline fixture",
        url=None,
        calendar_title="My bins",
        unique_id="fixture",
        day_offset=0,
    )
    records = list(catalogue({"paper": "Paper"}).values())
    records.append(SensorConfig(name="Custom paper", types=["paper"]).as_dict())
    records = initial.get("records", records)
    entry = entry_for(
        ha,
        {
            "sensors": records,
            "device_controls": initial.get("device_controls", False),
            "auto_add_types": initial.get("auto_add_types", False),
            **initial.get("options", {}),
        },
        version=initial.get("version", 4),
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
