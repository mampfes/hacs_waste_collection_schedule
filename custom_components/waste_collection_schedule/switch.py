"""Advanced device-page switches for Waste Collection Schedule sensors."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_ADD_DAYS_TO, CONF_SENSOR_ID, CONF_SENSORS, DOMAIN
from .sensor_config_helpers import (
    build_ui_sensor_control_unique_id,
    build_ui_sensor_device_identifier,
    build_updated_options_by_sensor_id,
)
from .wcs_coordinator import WCSCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up advanced switch entities for each configured waste sensor."""
    coordinator: WCSCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []

    for sensor_config in entry.options.get(CONF_SENSORS, []):
        sensor_id = sensor_config.get(CONF_SENSOR_ID)
        sensor_name = sensor_config.get(CONF_NAME, coordinator.shell.calendar_title)
        if not sensor_id:
            continue

        entities.append(
            WasteSensorConfigSwitch(
                entry,
                coordinator,
                sensor_id,
                sensor_name,
                key=CONF_ADD_DAYS_TO,
                key_suffix="days_to_attribute",
                label="Advanced: expose days-to attribute",
                icon="mdi:calendar-clock",
            )
        )

    async_add_entities(entities)


class WasteSensorConfigSwitch(SwitchEntity):
    """Switch entity for boolean waste sensor options."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WCSCoordinator,
        sensor_id: str,
        sensor_name: str,
        key: str,
        key_suffix: str,
        label: str,
        icon: str,
    ) -> None:
        self._entry = entry
        self._sensor_id = sensor_id
        self._key = key
        self._attr_name = label
        self._attr_unique_id = build_ui_sensor_control_unique_id(
            coordinator.shell.unique_id, sensor_id, key_suffix
        )
        device_identifier = build_ui_sensor_device_identifier(
            coordinator.shell.unique_id, sensor_id
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_identifier)},
            manufacturer=coordinator.shell.title,
            model="Waste Pickup Sensor",
            name=sensor_name,
            via_device=(DOMAIN, coordinator.shell.unique_id),
        )
        self._attr_icon = icon

    @property
    def sensor_config(self) -> Mapping[str, Any]:
        """Return the latest stored configuration for this sensor."""
        return next(
            sensor
            for sensor in self._entry.options.get(CONF_SENSORS, [])
            if sensor.get(CONF_SENSOR_ID) == self._sensor_id
        )

    @property
    def is_on(self) -> bool:
        """Return whether the config option is enabled."""
        return bool(self.sensor_config.get(self._key, False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the config option."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options=build_updated_options_by_sensor_id(
                self._entry,
                sensor_id=self._sensor_id,
                updates={self._key: True},
            ),
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the config option."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options=build_updated_options_by_sensor_id(
                self._entry,
                sensor_id=self._sensor_id,
                removals=(self._key,),
            ),
        )
