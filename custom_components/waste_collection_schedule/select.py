"""Device-page configuration selects for Waste Collection Schedule sensors."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_COUNT,
    CONF_COLLECTION_TYPES,
    CONF_DATE_TEMPLATE,
    CONF_DETAILS_FORMAT,
    CONF_EVENT_INDEX,
    CONF_LEADTIME,
    CONF_PRESET_LANGUAGE,
    CONF_SENSOR_ID,
    CONF_SENSORS,
    DOMAIN,
)
from .sensor import DetailsFormat
from .sensor_config_helpers import (
    build_ui_sensor_control_unique_id,
    build_ui_sensor_device_identifier,
    build_updated_options_by_sensor_id,
)
from .sensor_template_presets import (
    CUSTOM_OPTION,
    DATE_TEMPLATE_PRESETS,
    DEFAULT_OPTION,
    PRESET_LANGUAGE_OPTIONS,
    convert_value_template_language,
    get_preset_language_label,
    get_preset_language_value,
    get_preset_option,
    get_value_template_presets,
)
from .wcs_coordinator import WCSCoordinator

LAYOUT_LABELS = {
    DetailsFormat.upcoming.value: "Upcoming list",
    DetailsFormat.appointment_types.value: "By collection type",
    DetailsFormat.generic.value: "All attributes",
    DetailsFormat.hidden.value: "Hide details",
}
LAYOUT_VALUES = {label: value for value, label in LAYOUT_LABELS.items()}

COUNT_LABELS = {
    "Default": None,
    "1 pickup": 1,
    "2 pickups": 2,
    "3 pickups": 3,
    "5 pickups": 5,
    "10 pickups": 10,
    "20 pickups": 20,
}

LEADTIME_LABELS = {
    "Default": None,
    "1 day": 1,
    "3 days": 3,
    "7 days": 7,
    "14 days": 14,
    "30 days": 30,
    "60 days": 60,
}

EVENT_INDEX_LABELS = {
    "First matching pickup": 0,
    "Second matching pickup": 1,
    "Third matching pickup": 2,
    "Fourth matching pickup": 3,
    "Fifth matching pickup": 4,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up quick configuration selects for each configured waste sensor."""
    coordinator: WCSCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SelectEntity] = []

    for sensor_config in entry.options.get(CONF_SENSORS, []):
        sensor_id = sensor_config.get(CONF_SENSOR_ID)
        sensor_name = sensor_config.get(CONF_NAME, coordinator.shell.calendar_title)
        if not sensor_id:
            continue

        entities.extend(
            [
                WasteSensorLayoutSelect(entry, coordinator, sensor_id, sensor_name),
                WasteSensorLanguageSelect(entry, coordinator, sensor_id, sensor_name),
                WasteSensorTemplatePresetSelect(
                    entry,
                    coordinator,
                    sensor_id,
                    sensor_name,
                    key=CONF_VALUE_TEMPLATE,
                    key_suffix="state_preset",
                    label="State text",
                    icon="mdi:format-text",
                ),
                WasteSensorTemplatePresetSelect(
                    entry,
                    coordinator,
                    sensor_id,
                    sensor_name,
                    key=CONF_DATE_TEMPLATE,
                    key_suffix="date_preset",
                    label="Date format",
                    icon="mdi:calendar-text",
                ),
                WasteSensorNumberPresetSelect(
                    entry,
                    coordinator,
                    sensor_id,
                    sensor_name,
                    key=CONF_COUNT,
                    key_suffix="count",
                    label="Advanced: upcoming count",
                    options=COUNT_LABELS,
                    default_option="Default",
                    icon="mdi:counter",
                ),
                WasteSensorNumberPresetSelect(
                    entry,
                    coordinator,
                    sensor_id,
                    sensor_name,
                    key=CONF_LEADTIME,
                    key_suffix="leadtime",
                    label="Advanced: lead time",
                    options=LEADTIME_LABELS,
                    default_option="Default",
                    icon="mdi:calendar-range",
                ),
                WasteSensorNumberPresetSelect(
                    entry,
                    coordinator,
                    sensor_id,
                    sensor_name,
                    key=CONF_EVENT_INDEX,
                    key_suffix="event_index",
                    label="Advanced: pickup to show",
                    options=EVENT_INDEX_LABELS,
                    default_option="First matching pickup",
                    icon="mdi:format-list-numbered",
                ),
            ]
        )

    async_add_entities(entities)


class WasteSensorConfigEntity:
    """Common behavior for per-sensor configuration entities."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WCSCoordinator,
        sensor_id: str,
        sensor_name: str,
        key_suffix: str,
        display_name: str,
        icon: str | None = None,
        enabled_default: bool = True,
    ) -> None:
        self._entry = entry
        self._coordinator = coordinator
        self._sensor_id = sensor_id
        self._attr_name = display_name
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
        if icon:
            self._attr_icon = icon
        if not enabled_default:
            self._attr_entity_registry_enabled_default = False

    @property
    def sensor_config(self) -> Mapping[str, Any]:
        """Return the latest stored configuration for this sensor."""
        return next(
            sensor
            for sensor in self._entry.options.get(CONF_SENSORS, [])
            if sensor.get(CONF_SENSOR_ID) == self._sensor_id
        )

    async def _async_save(
        self,
        updates: dict[str, Any] | None = None,
        removals: tuple[str, ...] = (),
    ) -> None:
        """Persist the updated sensor configuration."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options=build_updated_options_by_sensor_id(
                self._entry,
                sensor_id=self._sensor_id,
                updates=updates,
                removals=removals,
            ),
        )


class WasteSensorLayoutSelect(WasteSensorConfigEntity, SelectEntity):
    """Select for choosing the more-info layout of a waste sensor."""

    _attr_options = list(LAYOUT_VALUES.keys())

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WCSCoordinator,
        sensor_id: str,
        sensor_name: str,
    ) -> None:
        super().__init__(
            entry,
            coordinator,
            sensor_id,
            sensor_name,
            key_suffix="details_format",
            display_name="Display mode",
            icon="mdi:view-list",
        )

    @property
    def current_option(self) -> str | None:
        """Return the current display mode label."""
        current = self.sensor_config.get(
            CONF_DETAILS_FORMAT, DetailsFormat.upcoming.value
        )
        if isinstance(current, DetailsFormat):
            current = current.value
        return LAYOUT_LABELS.get(str(current), "Upcoming list")

    async def async_select_option(self, option: str) -> None:
        """Persist the selected display mode."""
        await self._async_save(updates={CONF_DETAILS_FORMAT: LAYOUT_VALUES[option]})


class WasteSensorLanguageSelect(WasteSensorConfigEntity, SelectEntity):
    """Select for choosing the language used by display presets."""

    _attr_options = list(PRESET_LANGUAGE_OPTIONS.keys())

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WCSCoordinator,
        sensor_id: str,
        sensor_name: str,
    ) -> None:
        super().__init__(
            entry,
            coordinator,
            sensor_id,
            sensor_name,
            key_suffix="preset_language",
            display_name="Display language",
            icon="mdi:translate",
        )

    @property
    def current_option(self) -> str | None:
        """Return the selected display preset language label."""
        return get_preset_language_label(self.sensor_config.get(CONF_PRESET_LANGUAGE))

    async def async_select_option(self, option: str) -> None:
        """Persist the display language and translate known state presets."""
        language = get_preset_language_value(option)
        updates = {CONF_PRESET_LANGUAGE: language}
        converted_template = convert_value_template_language(
            self.sensor_config.get(CONF_VALUE_TEMPLATE), language
        )
        if converted_template is not None:
            updates[CONF_VALUE_TEMPLATE] = converted_template

        await self._async_save(updates=updates)


class WasteSensorTemplatePresetSelect(WasteSensorConfigEntity, SelectEntity):
    """Select for applying a preset template to a waste sensor field."""

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
        enabled_default: bool = True,
    ) -> None:
        super().__init__(
            entry,
            coordinator,
            sensor_id,
            sensor_name,
            key_suffix=key_suffix,
            display_name=label,
            icon=icon,
            enabled_default=enabled_default,
        )
        self._key = key

    @property
    def presets(self) -> dict[str, str]:
        """Return the presets for the current sensor language and field."""
        if self._key == CONF_VALUE_TEMPLATE:
            collection_types = self.sensor_config.get(CONF_COLLECTION_TYPES)
            return get_value_template_presets(
                self.sensor_config.get(CONF_PRESET_LANGUAGE),
                grouped=not collection_types or len(collection_types) > 1,
            )
        return DATE_TEMPLATE_PRESETS

    @property
    def options(self) -> list[str]:
        """Return the available preset labels."""
        return [DEFAULT_OPTION, *self.presets.keys(), CUSTOM_OPTION]

    @property
    def current_option(self) -> str | None:
        """Return the current matching preset, default, or custom."""
        return get_preset_option(self.sensor_config.get(self._key), self.presets)

    async def async_select_option(self, option: str) -> None:
        """Apply a preset to the underlying sensor option."""
        if option == CUSTOM_OPTION:
            return
        if option == DEFAULT_OPTION:
            await self._async_save(removals=(self._key,))
            return
        await self._async_save(updates={self._key: self.presets[option]})


class WasteSensorNumberPresetSelect(WasteSensorConfigEntity, SelectEntity):
    """Advanced select for numeric sensor options that can be reset to default."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WCSCoordinator,
        sensor_id: str,
        sensor_name: str,
        key: str,
        key_suffix: str,
        label: str,
        options: dict[str, int | None],
        default_option: str,
        icon: str,
    ) -> None:
        super().__init__(
            entry,
            coordinator,
            sensor_id,
            sensor_name,
            key_suffix=key_suffix,
            display_name=label,
            icon=icon,
            enabled_default=False,
        )
        self._key = key
        self._options = options
        self._default_option = default_option
        self._attr_options = list(options.keys())

    @property
    def current_option(self) -> str | None:
        """Return the label matching the stored numeric option."""
        current = self.sensor_config.get(self._key)
        for label, value in self._options.items():
            if current == value:
                return label
        return self._default_option

    async def async_select_option(self, option: str) -> None:
        """Persist the selected numeric option."""
        value = self._options[option]
        if value is None:
            await self._async_save(removals=(self._key,))
            return
        await self._async_save(updates={self._key: value})
