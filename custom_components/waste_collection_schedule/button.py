"""Device-page actions for Waste Collection Schedule sensors."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    CONF_DEVICE_SENSOR_CONTROLS,
    CONF_SENSORS,
    DOMAIN,
    UPDATE_SENSORS_SIGNAL,
)
from .sensor_config_helpers import (
    build_added_collection_type_sensor_options,
    build_added_combined_sensor_options,
    build_create_combined_ui_sensor_action_unique_id,
    build_create_ui_sensor_action_unique_id,
    has_combined_sensor,
    missing_collection_types,
)
from .wcs_coordinator import WCSCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up creation action buttons for waste pickup sensors."""
    if not entry.options.get(CONF_DEVICE_SENSOR_CONTROLS, False):
        return

    coordinator: WCSCoordinator = hass.data[DOMAIN][entry.entry_id]
    added_action_ids: set[str] = set()

    @callback
    def add_missing_buttons() -> None:
        """Add creation actions discovered after any successful fetch."""
        sensors = entry.options.get(CONF_SENSORS, [])
        entities: list[ButtonEntity] = []

        combined_action_id = build_create_combined_ui_sensor_action_unique_id(
            coordinator.shell.unique_id
        )
        if (
            not has_combined_sensor(sensors)
            and combined_action_id not in added_action_ids
        ):
            added_action_ids.add(combined_action_id)
            entities.append(CreateCombinedWasteSensorButton(entry, coordinator))

        for collection_type_id, display_name in missing_collection_types(
            coordinator._aggregator.type_options,
            sensors,
        ):
            action_id = build_create_ui_sensor_action_unique_id(
                coordinator.shell.unique_id,
                collection_type_id,
            )
            if action_id in added_action_ids:
                continue
            added_action_ids.add(action_id)
            entities.append(
                CreateWasteSensorButton(
                    entry,
                    coordinator,
                    collection_type_id,
                    display_name,
                )
            )

        if entities:
            async_add_entities(entities)

    add_missing_buttons()
    entry.async_on_unload(
        async_dispatcher_connect(hass, UPDATE_SENSORS_SIGNAL, add_missing_buttons)
    )


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
        self._attr_unique_id = build_create_combined_ui_sensor_action_unique_id(
            coordinator.shell.unique_id
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
        collection_type_id: str,
        display_name: str,
    ) -> None:
        self._entry = entry
        self._collection_type_id = collection_type_id
        self._display_name = display_name
        self._attr_name = f"Create {display_name} sensor"
        self._attr_unique_id = build_create_ui_sensor_action_unique_id(
            coordinator.shell.unique_id, collection_type_id
        )
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Create the waste sensor and let the config entry reload."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options=build_added_collection_type_sensor_options(
                self._entry,
                self._collection_type_id,
                self._display_name,
            ),
        )
