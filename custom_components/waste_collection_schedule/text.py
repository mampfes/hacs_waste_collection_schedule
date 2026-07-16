"""Advanced device-page text configuration for Waste Collection Schedule sensors."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_DATE_TEMPLATE, CONF_SENSOR_ID, CONF_SENSORS, DOMAIN
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
    """Set up advanced template text entities for each configured waste sensor."""
    coordinator: WCSCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[TextEntity] = []

    for sensor_config in entry.options.get(CONF_SENSORS, []):
        sensor_id = sensor_config.get(CONF_SENSOR_ID)
        sensor_name = sensor_config.get(CONF_NAME, coordinator.shell.calendar_title)
        if not sensor_id:
            continue

        entities.extend(
            [
                WasteSensorTemplateText(
                    entry,
                    coordinator,
                    sensor_id,
                    sensor_name,
                    key=CONF_VALUE_TEMPLATE,
                    key_suffix="state_template",
                    label="Advanced: custom state template",
                    icon="mdi:code-braces",
                ),
                WasteSensorTemplateText(
                    entry,
                    coordinator,
                    sensor_id,
                    sensor_name,
                    key=CONF_DATE_TEMPLATE,
                    key_suffix="date_template",
                    label="Advanced: custom date template",
                    icon="mdi:calendar-edit",
                ),
            ]
        )

    async_add_entities(entities)


class WasteSensorTemplateText(TextEntity):
    """Text entity for editing a waste sensor template directly from its device."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_has_entity_name = True
    _attr_native_min = 0
    _attr_native_max = 500

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
            (
                sensor
                for sensor in self._entry.options.get(CONF_SENSORS, [])
                if sensor.get(CONF_SENSOR_ID) == self._sensor_id
            ),
            {},
        )

    @property
    def native_value(self) -> str:
        """Return the current template string."""
        return str(self.sensor_config.get(self._key, ""))

    async def async_set_value(self, value: str) -> None:
        """Persist the edited template string."""
        if value.strip():
            cv.template(value)
            options = build_updated_options_by_sensor_id(
                self._entry,
                sensor_id=self._sensor_id,
                updates={self._key: value},
            )
        else:
            options = build_updated_options_by_sensor_id(
                self._entry,
                sensor_id=self._sensor_id,
                removals=(self._key,),
            )

        self.hass.config_entries.async_update_entry(self._entry, options=options)
