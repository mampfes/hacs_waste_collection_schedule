"""Sensor platform support for Waste Collection Schedule."""

import datetime
import logging
from enum import Enum
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE
from homeassistant.core import HomeAssistant, callback
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
    CONF_SENSORS,
    CONF_SOURCE_INDEX,
    DOMAIN,
    ICON_GENERAL_TRASH,
    UPDATE_SENSORS_SIGNAL,
)
from .waste_collection_api import WasteCollectionApi
from .waste_collection_schedule import Collection, CollectionGroup
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
        if isinstance(details_format, str):
            details_format = DetailsFormat(details_format)

        entities.append(
            ScheduleSensor(
                hass=hass,
                api=None,
                coordinator=coordinator,
                name=sensor.get(CONF_NAME, coordinator.shell.calendar_title),
                aggregator=aggregator,
                details_format=details_format,
                count=sensor.get(CONF_COUNT),
                leadtime=sensor.get(CONF_LEADTIME),
                collection_types=sensor.get(CONF_COLLECTION_TYPES),
                value_template=value_template,
                date_template=date_template,
                add_days_to=sensor.get(CONF_ADD_DAYS_TO, False),
                event_index=sensor.get(CONF_EVENT_INDEX),
            )
        )

    async_add_entities(entities, update_before_add=True)


# YAML setup
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

    date_template = config.get(CONF_DATE_TEMPLATE)
    if date_template is not None:
        date_template.hass = hass

    if DOMAIN not in hass.data:
        raise Exception(
            "Waste Collection Schedule integration not set up, please check you configured a source in your configuration.yaml"
        )

    api = hass.data[DOMAIN].get("YAML_CONFIG")

    # create aggregator for all sources
    source_index = config[CONF_SOURCE_INDEX]
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

    entities = []

    entities.append(
        ScheduleSensor(
            hass=hass,
            api=api,
            coordinator=None,
            name=config[CONF_NAME],
            aggregator=aggregator,
            details_format=config[CONF_DETAILS_FORMAT],
            count=config.get(CONF_COUNT),
            leadtime=config.get(CONF_LEADTIME),
            collection_types=config.get(CONF_COLLECTION_TYPES),
            value_template=value_template,
            date_template=date_template,
            add_days_to=config.get(CONF_ADD_DAYS_TO),
            event_index=config.get(CONF_EVENT_INDEX),
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
        aggregator: CollectionAggregator,
        details_format: DetailsFormat,
        count: int | None,
        leadtime: int | None,
        collection_types: list[str] | None,
        value_template: Template | None,
        date_template: Template | None,
        add_days_to: bool,
        event_index: int | None,
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

        self._value: Any = None

        # entity attributes
        self._attr_name = name
        if self._coordinator:
            shell = self._coordinator.shell
            self._attr_unique_id = f"{shell.unique_id}_ui_sensor_{name}"
            self._attr_device_info = self._coordinator.device_info
        else:
            self._attr_unique_id = name
        self._attr_should_poll = False

        async_dispatcher_connect(hass, UPDATE_SENSORS_SIGNAL, self._update_sensor)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

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
        else:
            return self._coordinator.separator

    @property
    def _include_today(self):
        """Return true if collections for today shall be included in the results."""
        if self._api:
            return datetime.datetime.now().time() < self._api._day_switch_time
        else:
            return datetime.datetime.now().time() < self._coordinator.day_switch_time

    def _add_refreshtime(self):
        """Add refresh-time (= last fetch time) to device-state-attributes."""
        refreshtime = ""
        if self._aggregator.refreshtime is not None:
            refreshtime = self._aggregator.refreshtime.strftime("%x %X")
        self._attr_attribution = f"Last update: {refreshtime}"

    def _set_state(self, upcoming: list[CollectionGroup]):
        """Set entity state with default format."""
        if len(upcoming) == 0:
            self._value = None
            self._attr_icon = ICON_GENERAL_TRASH
            self._attr_entity_picture = None
            return

        collection = upcoming[0]
        # collection::=CollectionGroup{date=2020-04-01, types=['Type1', 'Type2']}

        if self._value_template is not None:
            self._value = self._value_template.async_render_with_possible_json_value(
                collection, None
            )
        else:
            self._value = (
                f"{self._separator.join(collection.types)} in {collection.daysTo} days"
            )

        self._attr_icon = collection.icon or ICON_GENERAL_TRASH
        self._attr_entity_picture = collection.picture

    def _render_date(self, collection: Collection):
        if self._date_template is not None:
            return self._date_template.async_render_with_possible_json_value(
                collection, None
            )
        else:
            return collection.date.isoformat()

    @callback
    def _update_sensor(self):
        """Update the state and the device-state-attributes of the entity.

        Called if a new data has been fetched from the source.
        """
        if self._aggregator is None:
            return None

        upcoming1 = self._aggregator.get_upcoming_group_by_day(
            count=1,
            include_types=self._collection_types,
            include_today=self._include_today,
            start_index=self._event_index,
        )

        self._set_state(upcoming1)

        attributes = {}

        collection_types = (
            sorted(self._aggregator.types)
            if self._collection_types is None
            else self._collection_types
        )

        if self._details_format == DetailsFormat.upcoming:
            # show upcoming events list in details
            upcoming = self._aggregator.get_upcoming_group_by_day(
                count=self._count,
                leadtime=self._leadtime,
                include_types=self._collection_types,
                include_today=self._include_today,
                start_index=self._event_index,
            )
            for collection in upcoming:
                attributes[self._render_date(collection)] = self._separator.join(
                    collection.types
                )
        elif self._details_format == DetailsFormat.appointment_types:
            # show list of collections in details
            for t in collection_types:
                collections = self._aggregator.get_upcoming(
                    count=1,
                    include_types=[t],
                    include_today=self._include_today,
                    start_index=self._event_index,
                )
                date = (
                    "" if len(collections) == 0 else self._render_date(collections[0])
                )
                attributes[t] = date
        elif self._details_format == DetailsFormat.generic:
            # insert generic attributes into details
            attributes["types"] = collection_types
            attributes["upcoming"] = self._aggregator.get_upcoming(
                count=self._count,
                leadtime=self._leadtime,
                include_types=self._collection_types,
                include_today=self._include_today,
            )
            refreshtime = ""
            if self._aggregator.refreshtime is not None:
                refreshtime = self._aggregator.refreshtime.isoformat(timespec="seconds")
            attributes["last_update"] = refreshtime

        if len(upcoming1) > 0:
            if self._add_days_to:
                attributes["daysTo"] = upcoming1[0].daysTo

        self._attr_extra_state_attributes = attributes
        self._add_refreshtime()

        if self.hass is not None:
            self.async_write_ha_state()
