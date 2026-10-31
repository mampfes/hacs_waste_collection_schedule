"""One lifecycle owner for options-flow and device-control sensor edits."""

import asyncio
from copy import deepcopy

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from .const import DOMAIN, UPDATE_SENSORS_SIGNAL
from .default_sensors import catalogue
from .sensor_model import SensorConfig

SENSOR_CONFIG_SIGNAL = "wcs_sensor_config"


def cleanup_sensor_devices(hass, entry, wanted):
    """Remove only our empty, retired sensor devices; preserve attached entities."""
    from homeassistant.helpers import device_registry as dr

    devices = dr.async_get(hass)
    registry = er.async_get(hass)
    prefix = entry.entry_id + "_sensor_"
    for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
        ids = [
            identifier.removeprefix(prefix)
            for domain, identifier in device.identifiers
            if domain == DOMAIN and identifier.startswith(prefix)
        ]
        if (
            ids
            and not any(sensor_id in wanted for sensor_id in ids)
            and not er.async_entries_for_device(
                registry, device.id, include_disabled_entities=True
            )
        ):
            devices.async_remove_device(device.id)


class SensorManager:
    def __init__(self, hass, coordinator, async_add_entities):
        self.hass = hass
        self.coordinator = coordinator
        self.entry = coordinator.config_entry
        self.add_entities = async_add_entities
        self.entities = {}
        self.options = deepcopy(dict(self.entry.options))
        self.data = deepcopy(dict(self.entry.data))
        self._lock = asyncio.Lock()

    @property
    def type_labels(self):
        from waste_collection_schedule.waste_types import ALL_TYPES, display_name

        customizations = self.entry.options.get("customize", {})
        labels = {
            e.waste_type.id: customizations.get(e.waste_type.id, {}).get("alias")
            or display_name(e.waste_type)
            for e in self.coordinator.shell._entries
        }
        known = {wt.id: display_name(wt) for wt in ALL_TYPES}
        for record in self.entry.options.get("sensors", []):
            if record["origin"].startswith("type:"):
                type_id = record["origin"].removeprefix("type:")
                label = known.get(
                    type_id, type_id.removeprefix("preserved:").removeprefix("legacy_")
                )
                labels.setdefault(
                    type_id, customizations.get(type_id, {}).get("alias") or label
                )
        return labels

    @property
    def catalogue(self):
        return catalogue(self.type_labels)

    async def async_setup(self):
        self.entry.async_on_unload(
            self.hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED, self._registry_changed
            )
        )
        self.entry.async_on_unload(
            async_dispatcher_connect(
                self.hass, UPDATE_SENSORS_SIGNAL, self._schedule_changed
            )
        )
        if self.entry.options.get("auto_add_types"):
            await self.async_add_discovered_types()
        await self.async_apply()

    @callback
    def _schedule_changed(self):
        if self.entry.options.get("auto_add_types"):
            self.hass.async_create_task(self.async_add_discovered_types())
        async_dispatcher_send(self.hass, SENSOR_CONFIG_SIGNAL + self.entry.entry_id)

    async def async_add_discovered_types(self):
        async with self._lock:
            records = list(self.entry.options.get("sensors", []))
            existing = {s["origin"] for s in records}
            records.extend(
                s
                for key, s in self.catalogue.items()
                if key.startswith("type:") and key not in existing
            )
            if records != self.entry.options.get("sensors", []):
                self.hass.config_entries.async_update_entry(
                    self.entry, options={**self.entry.options, "sensors": records}
                )

    async def async_apply(self):
        async with self._lock:
            await self._async_apply_locked()

    async def _async_apply_locked(self):
        from .sensor import create_sensor
        from .sensor_controls import CONTROL_KEYS

        options = deepcopy(dict(self.entry.options))
        previous = {r["id"]: r for r in self.options.get("sensors", [])}
        initializing = not self.entities
        records = [
            SensorConfig.from_dict(s).as_dict() for s in options.get("sensors", [])
        ]
        registry = er.async_get(self.hass)
        wanted = {s["id"] for s in records}
        for entity in er.async_entries_for_config_entry(registry, self.entry.entry_id):
            controls_prefix = self.entry.entry_id + "_control_"
            if entity.platform == DOMAIN and entity.unique_id.startswith(
                controls_prefix
            ):
                control_id = entity.unique_id.removeprefix(controls_prefix)
                match = next(
                    (
                        (s, key)
                        for s in records
                        for key in CONTROL_KEYS[s["kind"]]
                        | ({"delete"} if s["origin"] == "custom" else set())
                        if control_id == s["id"] + "_" + key
                    ),
                    None,
                )
                record, key = match if match else (None, "")
                if record is None or (
                    key not in CONTROL_KEYS[record["kind"]]
                    and not (key == "delete" and record["origin"] == "custom")
                ):
                    registry.async_remove(entity.entity_id)
                else:
                    if key in (
                        "event_index",
                        "value_template",
                        "date_template",
                        "color",
                    ) and entity.disabled_by in (
                        None,
                        er.RegistryEntryDisabler.INTEGRATION,
                    ):
                        registry.async_update_entity(
                            entity.entity_id,
                            disabled_by=None
                            if record["advanced"]
                            else er.RegistryEntryDisabler.INTEGRATION,
                        )

            prefix = self.entry.entry_id + "_sensor_"
            if (
                entity.domain == "sensor"
                and entity.platform == DOMAIN
                and entity.unique_id.startswith(prefix)
                and entity.unique_id.removeprefix(prefix) not in wanted
            ):
                registry.async_remove(entity.entity_id)
        for sensor_id in set(self.entities) - wanted:
            entity = self.entities.pop(sensor_id)
            if entity.hass is not None:
                await entity.async_remove()
        additions = []
        for record in records:
            entity = self.entities.get(record["id"])
            if entity is not None and entity._record["kind"] != record["kind"]:
                if entity.hass is not None:
                    await entity.async_remove()
                entity = None
            if entity is None:
                entity = create_sensor(self.hass, self.coordinator, record)
                self.entities[record["id"]] = entity
                additions.append(entity)
            else:
                entity.apply_config(record)
                if entity.hass is not None and entity.enabled:
                    entity._update_sensor()
            entity_id = registry.async_get_entity_id("sensor", DOMAIN, entity.unique_id)
            if entity_id:
                registered = registry.async_get(entity_id)
                disabled = (
                    None
                    if record["enabled"]
                    else registered.disabled_by or er.RegistryEntryDisabler.INTEGRATION
                )
                if disabled != registered.disabled_by and (
                    initializing
                    or record["enabled"]
                    != previous.get(record["id"], {}).get("enabled")
                ):
                    registry.async_update_entity(entity_id, disabled_by=disabled)
                registry.async_update_entity(entity_id, original_name=record["name"])
                if registered.device_id and self.entry.options.get("device_controls"):
                    from homeassistant.helpers import device_registry as dr

                    dr.async_get(self.hass).async_update_device(
                        registered.device_id, name=record["name"]
                    )
        if additions:
            self.add_entities(additions)
        cleanup_sensor_devices(self.hass, self.entry, wanted)
        self.options = options
        async_dispatcher_send(self.hass, SENSOR_CONFIG_SIGNAL + self.entry.entry_id)

    async def async_update(self, sensor_id, patch):
        async with self._lock:
            records = deepcopy(self.entry.options.get("sensors", []))
            record = next(s for s in records if s["id"] == sensor_id)
            if record["origin"] != "custom" and any(
                k in patch for k in ("id", "origin", "types", "kind")
            ):
                raise ValueError(
                    "Predefined sensor identity, kind and filter are fixed"
                )
            if "id" in patch or "origin" in patch:
                raise ValueError("Sensor identity is immutable")
            record.update(patch)
            record.update(SensorConfig.from_dict(record).as_dict())
            self.hass.config_entries.async_update_entry(
                self.entry, options={**self.entry.options, "sensors": records}
            )

    async def async_set_enabled(self, sensor_id, enabled):
        await self.async_update(sensor_id, {"enabled": enabled})

    async def async_add_from_catalogue(self, origin):
        async with self._lock:
            records = deepcopy(self.entry.options.get("sensors", []))
            record = next((s for s in records if s["origin"] == origin), None)
            if record:
                record["enabled"] = True
            else:
                offered = self.catalogue.get(origin)
                if offered is None:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN, translation_key="type_unavailable"
                    )
                records.append(offered)
            self.hass.config_entries.async_update_entry(
                self.entry, options={**self.entry.options, "sensors": records}
            )

    async def async_delete(self, sensor_id):
        async with self._lock:
            record = next(
                s for s in self.entry.options["sensors"] if s["id"] == sensor_id
            )
            if record["origin"] != "custom":
                raise ValueError(
                    "Predefined sensors can be disabled or reset, not deleted"
                )
            records = [s for s in self.entry.options["sensors"] if s["id"] != sensor_id]
            self.hass.config_entries.async_update_entry(
                self.entry, options={**self.entry.options, "sensors": records}
            )

    @callback
    def _registry_changed(self, event):
        if event.data.get("action") != "update" or "disabled_by" not in event.data.get(
            "changes", {}
        ):
            return
        entity = er.async_get(self.hass).async_get(event.data["entity_id"])
        if (
            not entity
            or entity.platform != DOMAIN
            or entity.config_entry_id != self.entry.entry_id
        ):
            return
        for record in self.entry.options.get("sensors", []):
            if entity.unique_id == f"{self.entry.entry_id}_sensor_{record['id']}":
                enabled = entity.disabled_by is None
                if record["enabled"] != enabled:
                    self.hass.async_create_task(
                        self.async_set_enabled(record["id"], enabled)
                    )
                return
