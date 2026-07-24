"""Sensor platform support for Waste Collection Schedule."""

import datetime
import logging
from enum import Enum
from typing import Any

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.template import Template

# fmt: off
from custom_components.waste_collection_schedule.waste_collection_schedule.collection_aggregator import (
    CollectionAggregator,
)

from .const import (
    CONF_ADD_DAYS_TO,
    CONF_COLLECTION_TYPES,
    CONF_COUNT,
    CONF_DATE_TEMPLATE,
    CONF_DETAILS_FORMAT,
    CONF_EVENT_INDEX,
    CONF_LEADTIME,
    CONF_PRESET_LANGUAGE,
    CONF_SENSOR_ID,
    CONF_SENSOR_LEGACY_UNIQUE_ID,
    CONF_SENSORS,
    CONF_SOURCE_INDEX,
    DOMAIN,
    UPDATE_SENSORS_SIGNAL,
)
from .sensor_config_helpers import (
    build_ui_sensor_device_identifier,
    build_ui_sensor_unique_id,
)
from .sensor_template_presets import format_default_state_text
from .waste_collection_api import WasteCollectionApi

# CollectionBase is the real Collection class; the exported `Collection` is a
# factory instance (not valid as a type annotation).
from .waste_collection_schedule import CollectionBase, CollectionGroup
from .wcs_coordinator import WCSCoordinator

# fmt: on


_LOGGER = logging.getLogger(__name__)


class DetailsFormat(Enum):
    """Values for CONF_DETAILS_FORMAT."""

    upcoming = "upcoming"  # list of "<date> <type1, type2, ...>"
    appointment_types = "appointment_types"  # list of "<type> <date>"
    generic = "generic"  # all values in separate attributes
    hidden = "hidden"  # hide details


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_SOURCE_INDEX, default=0): vol.Any(
            cv.positive_int, vol.All(cv.ensure_list, [cv.positive_int])
        ),  # can be a scalar or a list
        vol.Optional(CONF_DETAILS_FORMAT, default="upcoming"): cv.enum(DetailsFormat),
        vol.Optional(CONF_COUNT): cv.positive_int,
        vol.Optional(CONF_LEADTIME): cv.positive_int,
        vol.Optional(CONF_COLLECTION_TYPES): cv.ensure_list,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_DATE_TEMPLATE): cv.template,
        vol.Optional(CONF_ADD_DAYS_TO, default=False): cv.boolean,
        vol.Optional(CONF_EVENT_INDEX, default=0): cv.positive_int,
    }
)


def render_sensor_preview(
    aggregator: CollectionAggregator,
    separator: str,
    day_switch_time: datetime.time,
    details_format: DetailsFormat | None,
    count: int | None,
    leadtime: int | None,
    collection_types: list[str] | None,
    value_template: Template | None,
    date_template: Template | None,
    add_days_to: bool,
    event_index: int | None,
    preset_language: str | None = None,
) -> tuple[Any, dict[str, Any], str, str | None]:
    """Render the current sensor state and attributes for UI preview and entities."""
    details_format = details_format or DetailsFormat.upcoming
    include_today = dt_util.now().time() < day_switch_time

    upcoming1 = aggregator.get_upcoming_group_by_day(
        count=1,
        include_types=collection_types,
        include_today=include_today,
        start_index=event_index,
    )

    collection = upcoming1[0] if upcoming1 else None
    value: Any = None
    icon = "mdi:trash-can"
    picture = None
    if collection is not None:
        if value_template is not None:
            value = value_template.async_render_with_possible_json_value(
                collection, None
            )
        else:
            if preset_language is None:
                value = (
                    f"{separator.join(collection.types)} in {collection.daysTo} days"
                )
            else:
                value = format_default_state_text(
                    collection.types,
                    collection.daysTo,
                    separator,
                    preset_language,
                )
        icon = collection.icon or icon
        picture = collection.picture

    def render_date(entry: CollectionBase | CollectionGroup):
        if date_template is not None:
            return date_template.async_render_with_possible_json_value(entry, None)
        return entry.date.isoformat()

    attributes: dict[str, Any] = {}
    if collection_types is None:
        available_collection_types = [
            (display_name, display_name)
            for display_name in sorted(aggregator.types, key=str.casefold)
        ]
    else:
        available_collection_types = [
            (type_filter, aggregator.type_options.get(type_filter, type_filter))
            for type_filter in collection_types
        ]

    grouped_upcoming = aggregator.get_upcoming_group_by_day(
        count=count,
        leadtime=leadtime,
        include_types=collection_types,
        include_today=include_today,
        start_index=event_index,
    )

    if details_format == DetailsFormat.upcoming:
        for upcoming_collection in grouped_upcoming:
            attributes[render_date(upcoming_collection)] = separator.join(
                upcoming_collection.types
            )
    elif details_format == DetailsFormat.appointment_types:
        for waste_type, display_name in available_collection_types:
            collections = aggregator.get_upcoming(
                count=1,
                include_types=[waste_type],
                include_today=include_today,
                start_index=event_index,
            )
            attributes[display_name] = (
                "" if len(collections) == 0 else render_date(collections[0])
            )
    elif details_format == DetailsFormat.generic:
        attributes["types"] = [label for _, label in available_collection_types]
        attributes["upcoming"] = aggregator.get_upcoming(
            count=count,
            leadtime=leadtime,
            include_types=collection_types,
            include_today=include_today,
        )
        refreshtime = ""
        if aggregator.refreshtime is not None:
            refreshtime = aggregator.refreshtime.isoformat(timespec="seconds")
        attributes["last_update"] = refreshtime

    if add_days_to and collection is not None:
        attributes["daysTo"] = collection.daysTo

    return value, attributes, icon, picture


# Config flow setup
async def async_setup_entry(hass, config: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][config.entry_id]
    aggregator = CollectionAggregator([coordinator.shell])
    _LOGGER.debug("Adding sensors for %s", coordinator.shell.calendar_title)
    _LOGGER.debug("Config: %s", config)

    entities = []
    for sensor in config.options.get(CONF_SENSORS, []):
        _LOGGER.debug("Adding sensor %s", sensor)
        value_template = sensor.get(CONF_VALUE_TEMPLATE)
        date_template = sensor.get(CONF_DATE_TEMPLATE)
        try:
            value_template = cv.template(value_template)
        except vol.Invalid:  # should only happen if value_template = None, as it is already validated in the config flow if it is not None
            value_template = None
        try:
            date_template = cv.template(date_template)
        except vol.Invalid:  # should only happen if value_template = None, as it is already validated in the config flow if it is not None
            date_template = None
        details_format = sensor.get(CONF_DETAILS_FORMAT)
        if details_format is None:
            details_format = DetailsFormat.upcoming
        if isinstance(details_format, str):
            details_format = DetailsFormat(details_format)

        entities.append(
            ScheduleSensor(
                hass=hass,
                api=None,
                coordinator=coordinator,
                name=sensor.get(CONF_NAME, coordinator.shell.calendar_title),
                sensor_id=sensor.get(CONF_SENSOR_ID),
                preserve_legacy_unique_id=sensor.get(
                    CONF_SENSOR_LEGACY_UNIQUE_ID, False
                ),
                aggregator=aggregator,
                details_format=details_format,
                count=sensor.get(CONF_COUNT),
                leadtime=sensor.get(CONF_LEADTIME),
                collection_types=sensor.get(CONF_COLLECTION_TYPES),
                value_template=value_template,
                date_template=date_template,
                add_days_to=sensor.get(CONF_ADD_DAYS_TO, False),
                event_index=sensor.get(CONF_EVENT_INDEX),
                preset_language=sensor.get(CONF_PRESET_LANGUAGE),
            )
        )

    async_add_entities(entities, update_before_add=True)


# YAML setup (via discovery from waste_collection_schedule: sensors: or legacy sensor platform)
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    if discovery_info is not None:
        # New method: sensor loaded via discovery from waste_collection_schedule: sensors:
        api = discovery_info["api"]
        sensor_config = discovery_info["sensor_config"]
    else:
        # Legacy method: sensor: platform: waste_collection_schedule
        _LOGGER.warning(
            "Configuration of waste_collection_schedule sensors via "
            "'sensor: platform: waste_collection_schedule' is deprecated and will be "
            "removed in a future version. Please move your sensor configuration into "
            "the 'sensors:' key under 'waste_collection_schedule:' in your "
            "configuration.yaml"
        )
        sensor_config = config

        if DOMAIN not in hass.data:
            raise Exception(
                "Waste Collection Schedule integration not set up, please check you configured a source in your configuration.yaml"
            )

        api = hass.data[DOMAIN].get("YAML_CONFIG")

        if api is None:
            raise Exception(
                "Waste Collection Schedule YAML configuration not found, please check you have configured sources under waste_collection_schedule: in your configuration.yaml"
            )

    value_template = sensor_config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        if not isinstance(value_template, Template):
            value_template = cv.template(value_template)
        value_template.hass = hass

    date_template = sensor_config.get(CONF_DATE_TEMPLATE)
    if date_template is not None:
        if not isinstance(date_template, Template):
            date_template = cv.template(date_template)
        date_template.hass = hass

    # create aggregator for all sources
    source_index = sensor_config.get(CONF_SOURCE_INDEX, 0)
    if not isinstance(source_index, list):
        source_index = [source_index]

    shells = []
    for i in source_index:
        shell = api.get_shell(i)
        if shell is None:
            raise ValueError(
                f"source_index {i} out of range (0-{len(api.shells) - 1}) please check your sensor configuration"
            )
        shells.append(shell)

    aggregator = CollectionAggregator(shells)

    details_format = sensor_config.get(CONF_DETAILS_FORMAT, "upcoming")
    if isinstance(details_format, str):
        details_format = DetailsFormat(details_format)

    entities = []

    entities.append(
        ScheduleSensor(
            hass=hass,
            api=api,
            coordinator=None,
            name=sensor_config[CONF_NAME],
            sensor_id=sensor_config.get(CONF_SENSOR_ID),
            preserve_legacy_unique_id=False,
            aggregator=aggregator,
            details_format=details_format,
            count=sensor_config.get(CONF_COUNT),
            leadtime=sensor_config.get(CONF_LEADTIME),
            collection_types=sensor_config.get(CONF_COLLECTION_TYPES),
            value_template=value_template,
            date_template=date_template,
            add_days_to=sensor_config.get(CONF_ADD_DAYS_TO, False),
            event_index=sensor_config.get(CONF_EVENT_INDEX, 0),
            preset_language=sensor_config.get(CONF_PRESET_LANGUAGE),
        )
    )

    async_add_entities(entities)


class ScheduleSensor(SensorEntity):
    """Base for sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: WasteCollectionApi | None,
        coordinator: WCSCoordinator | None,
        name: str,
        sensor_id: str | None,
        preserve_legacy_unique_id: bool,
        aggregator: CollectionAggregator,
        details_format: DetailsFormat,
        count: int | None,
        leadtime: int | None,
        collection_types: list[str] | None,
        value_template: Template | None,
        date_template: Template | None,
        add_days_to: bool,
        event_index: int | None,
        preset_language: str | None = None,
    ):
        """Initialize the entity."""
        self._api = api
        self._coordinator = coordinator
        self._aggregator = aggregator
        self._details_format = details_format
        self._count = count
        self._leadtime = leadtime
        self._collection_types = collection_types
        self._value_template = value_template
        self._date_template = date_template
        self._add_days_to = add_days_to
        self._event_index = event_index
        self._preset_language = preset_language
        self._sensor_id = sensor_id

        self._value: Any = None

        # entity attributes
        self._attr_name = name
        if self._coordinator:
            shell = self._coordinator.shell
            self._attr_unique_id = build_ui_sensor_unique_id(
                shell.unique_id,
                name,
                sensor_id,
                preserve_legacy_unique_id,
            )
            if sensor_id:
                device_identifier = build_ui_sensor_device_identifier(
                    shell.unique_id, sensor_id
                )
                self._attr_device_info = DeviceInfo(
                    identifiers={(DOMAIN, device_identifier)},
                    manufacturer=shell.title,
                    model="Waste Pickup Sensor",
                    name=name,
                    via_device=(DOMAIN, shell.unique_id),
                )
            else:
                self._attr_device_info = self._coordinator.device_info
        else:
            self._attr_unique_id = name
        self._attr_should_poll = False

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, UPDATE_SENSORS_SIGNAL, self._update_sensor
            )
        )

        if self._coordinator:
            self.async_on_remove(
                self._coordinator.async_add_listener(self._update_sensor, None)
            )

        self._update_sensor()

    @property
    def native_value(self):
        """Return the state of the entity."""
        return self._value

    @property
    def _separator(self):
        """Return separator string used to join waste types."""
        if self._api:
            return self._api.separator
        return self._coordinator.separator

    @property
    def _include_today(self):
        """Return true if collections for today shall be included in the results."""
        if self._api:
            return dt_util.now().time() < self._api._day_switch_time
        return dt_util.now().time() < self._coordinator.day_switch_time

    def _add_refreshtime(self):
        """Add refresh-time (= last fetch time) to device-state-attributes."""
        refreshtime = ""
        if self._aggregator.refreshtime is not None:
            refreshtime = self._aggregator.refreshtime.strftime("%x %X")
        self._attr_attribution = f"Last update: {refreshtime}"

    @callback
    def _update_sensor(self):
        """Update the state and the device-state-attributes of the entity.

        Called if a new data has been fetched from the source.
        """
        if self._aggregator is None:
            return
        (
            self._value,
            self._attr_extra_state_attributes,
            self._attr_icon,
            self._attr_entity_picture,
        ) = render_sensor_preview(
            aggregator=self._aggregator,
            separator=self._separator,
            day_switch_time=(
                self._api._day_switch_time
                if self._api
                else self._coordinator.day_switch_time
            ),
            details_format=self._details_format,
            count=self._count,
            leadtime=self._leadtime,
            collection_types=self._collection_types,
            value_template=self._value_template,
            date_template=self._date_template,
            add_days_to=self._add_days_to,
            event_index=self._event_index,
            preset_language=self._preset_language,
        )
        self._add_refreshtime()

        if self.hass is not None:
            self.async_write_ha_state()
