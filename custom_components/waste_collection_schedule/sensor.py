"""Sensor platform support for Waste Collection Schedule."""

import datetime
import logging
from enum import Enum

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

# fmt: off
from custom_components.waste_collection_schedule.waste_collection_schedule.collection_aggregator import \
    CollectionAggregator

from .const import DOMAIN, UPDATE_SENSORS_SIGNAL

# fmt: on


_LOGGER = logging.getLogger(__name__)

CONF_SOURCE_INDEX = "source_index"
CONF_DETAILS_FORMAT = "details_format"
CONF_COUNT = "count"
CONF_LEADTIME = "leadtime"
CONF_DATE_TEMPLATE = "date_template"
CONF_COLLECTION_TYPES = "types"
CONF_ADD_DAYS_TO = "add_days_to"
CONF_EVENT_INDEX = "event_index"


class DetailsFormat(Enum):
    """Values for CONF_DETAILS_FORMAT."""

    upcoming = "upcoming"  # list of "<date> <type1, type2, ...>"
    appointment_types = "appointment_types"  # list of "<type> <date>"
    generic = "generic"  # all values in separate attributes
    hidden = "hidden" # hide details


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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

    date_template = config.get(CONF_DATE_TEMPLATE)
    if date_template is not None:
        date_template.hass = hass

    api = hass.data[DOMAIN]

    # create aggregator for all sources
    source_index = config[CONF_SOURCE_INDEX]
    if not isinstance(source_index, list):
        source_index = [source_index]
    aggregator = CollectionAggregator([api.get_shell(i) for i in source_index])

    entities = []

    entities.append(
        ScheduleSensor(
            hass=hass,
            api=api,
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
        hass,
        api,
        name,
        aggregator,
        details_format,
        count,
        leadtime,
        collection_types,
        value_template,
        date_template,
        add_days_to,
        event_index,
    ):
        """Initialize the entity."""
        self._api = api
        self._aggregator = aggregator
        self._details_format = details_format
        self._count = count
        self._leadtime = leadtime
        self._collection_types = collection_types
        self._value_template = value_template
        self._date_template = date_template
        self._add_days_to = add_days_to
        self._event_index = event_index

        self._value = None

        # entity attributes
        self._attr_name = name
        self._attr_unique_id = name
        self._attr_should_poll = False

        async_dispatcher_connect(hass, UPDATE_SENSORS_SIGNAL, self._update_sensor)

    @property
    def native_value(self):
        """Return the state of the entity."""
        return self._value

    async def async_added_to_hass(self):
        """Entities have been added to hass."""
        self._update_sensor()

    @property
    def _separator(self):
        """Return separator string used to join waste types."""
        return self._api.separator

    @property
    def _include_today(self):
        """Return true if collections for today shall be included in the results."""
        return datetime.datetime.now().time() < self._api._day_switch_time

    def _add_refreshtime(self):
        """Add refresh-time (= last fetch time) to device-state-attributes."""
        refreshtime = ""
        if self._aggregator.refreshtime is not None:
            refreshtime = self._aggregator.refreshtime.strftime("%x %X")
        self._attr_attribution = f"Last update: {refreshtime}"

    def _set_state(self, upcoming):
        """Set entity state with default format."""
        if len(upcoming) == 0:
            self._value = None
            self._attr_icon = "mdi:trash-can"
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

        self._attr_icon = collection.icon or "mdi:trash-can"
        self._attr_entity_picture = collection.picture

    def _render_date(self, collection):
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
