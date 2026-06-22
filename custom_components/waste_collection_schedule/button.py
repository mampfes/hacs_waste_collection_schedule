"""Device-page actions for Waste Collection Schedule sensors."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_SENSORS, DOMAIN
from .sensor_config_helpers import (
    build_added_combined_sensor_options,
    build_added_collection_type_sensor_options,
    has_combined_sensor,
    missing_collection_types,
)
from .wcs_coordinator import WCSCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up creation action buttons for waste pickup sensors."""
    coordinator: WCSCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = entry.options.get(CONF_SENSORS, [])
    entities: list[ButtonEntity] = []

    if not has_combined_sensor(sensors):
        entities.append(CreateCombinedWasteSensorButton(entry, coordinator))

    for collection_type in missing_collection_types(
        coordinator._aggregator.types,
        sensors,
        coordinator.shell._customize,
    ):
        entities.append(CreateWasteSensorButton(entry, coordinator, collection_type))

    async_add_entities(entities)


class CreateCombinedWasteSensorButton(ButtonEntity):
    """Button that creates one all-types waste pickup sensor."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_icon = "mdi:trash-can"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WCSCoordinator,
    ) -> None:
        self._entry = entry
        self._attr_name = "Create combined next pickup sensor"
        self._attr_unique_id = (
            f"{coordinator.shell.unique_id}_ui_sensor_action_create_combined"
        )
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Create the combined waste sensor and let the config entry reload."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options=build_added_combined_sensor_options(self._entry),
        )


class CreateWasteSensorButton(ButtonEntity):
    """Button that creates a per-type waste pickup sensor."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_icon = "mdi:plus-circle"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WCSCoordinator,
        collection_type: str,
    ) -> None:
        self._entry = entry
        self._collection_type = collection_type
        self._attr_name = f"Create {collection_type} sensor"
        self._attr_unique_id = (
            f"{coordinator.shell.unique_id}_ui_sensor_action_create_{collection_type}"
        )
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Create the waste sensor and let the config entry reload."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options=build_added_collection_type_sensor_options(
                self._entry, self._collection_type
            ),
        )
