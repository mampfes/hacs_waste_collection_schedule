"""Sensor platform support for Waste Collection Schedule."""

import logging
from copy import copy
from enum import Enum
from typing import Any

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
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
    CONF_SOURCE_INDEX,
    DOMAIN,
    UPDATE_SENSORS_SIGNAL,
)

# fmt: on
from .sensor_format import async_prepare_formats
from .sensor_schema import yaml_sensor_fields
from .waste_collection_api import WasteCollectionApi

# CollectionBase is the real Collection class; the exported `Collection` is a
# factory instance (not valid as a type annotation).
from .waste_collection_schedule import CollectionBase, CollectionGroup, Icons
from .wcs_coordinator import WCSCoordinator

_LOGGER = logging.getLogger(__name__)


class DetailsFormat(Enum):
    """Values for CONF_DETAILS_FORMAT."""

    upcoming = "upcoming"  # list of "<date> <type1, type2, ...>"
    appointment_types = "appointment_types"  # list of "<type> <date>"
    generic = "generic"  # all values in separate attributes
    hidden = "hidden"  # hide details


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        **yaml_sensor_fields(),
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
    await async_prepare_formats(hass)
    coordinator = hass.data[DOMAIN][config.entry_id]
    from .sensor_manager import SensorManager

    manager = SensorManager(hass, coordinator, async_add_entities)
    coordinator.sensor_manager = manager
    await manager.async_setup()


def create_sensor(hass, coordinator, record):
    return SENSOR_CLASSES.get(record["kind"], ScheduleSensor)(
        hass=hass,
        api=None,
        coordinator=coordinator,
        name=record["name"],
        aggregator=coordinator._aggregator,
        details_format=DetailsFormat(record["details_format"]),
        count=record.get("count"),
        leadtime=record.get("leadtime"),
        collection_types=record.get("types"),
        value_template=None,
        date_template=None,
        add_days_to=False,
        event_index=record.get("event_index", 0),
        record=record,
    )


# YAML setup (via discovery from waste_collection_schedule: sensors: or legacy sensor platform)
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await async_prepare_formats(hass)
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

    if sensor_config.get(CONF_ADD_DAYS_TO) and not hass.data.setdefault(DOMAIN, {}).get(
        "_warned_add_days_to"
    ):
        _LOGGER.warning(
            "add_days_to is deprecated and ignored; daysTo is always available"
        )
        hass.data[DOMAIN]["_warned_add_days_to"] = True
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
        SENSOR_CLASSES.get(sensor_config.get("kind"), ScheduleSensor)(
            hass=hass,
            api=api,
            coordinator=None,
            name=sensor_config[CONF_NAME],
            aggregator=aggregator,
            details_format=details_format,
            count=sensor_config.get(CONF_COUNT),
            leadtime=sensor_config.get(CONF_LEADTIME),
            collection_types=sensor_config.get(CONF_COLLECTION_TYPES),
            value_template=value_template,
            date_template=date_template,
            add_days_to=sensor_config.get(CONF_ADD_DAYS_TO, False),
            event_index=sensor_config.get(CONF_EVENT_INDEX, 0),
            record=sensor_config,
        )
    )

    async_add_entities(entities)


class ScheduleSensor(SensorEntity):
    """Base for sensors."""

    _unrecorded_attributes = frozenset({"collections", "upcoming"})

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
        record: dict | None = None,
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
            entry_id = self._coordinator.config_entry.entry_id
            self._attr_unique_id = f"{entry_id}_ui_sensor_{name}"
            self._attr_device_info = self._coordinator.device_info
        else:
            self._attr_unique_id = name
        self._attr_should_poll = False

        self._record: dict[str, Any] = {}
        if record is not None:
            self.apply_config(record)

    def apply_config(self, record):
        """Apply a shared saved record without replacing the entity or fetching."""
        self._record = record
        self._attr_name = record["name"]
        self._details_format = DetailsFormat(record.get("details_format", "upcoming"))
        self._count = record.get("count")
        self._leadtime = record.get("leadtime")
        self._collection_types = record.get("types") or None
        self._event_index = record.get("event_index", 0)
        self._template_error = False
        self._attr_available = True
        for key in ("value_template", "date_template"):
            value = record.get(key)
            try:
                template = (
                    value
                    if isinstance(value, Template)
                    else cv.template(value)
                    if value
                    else None
                )
                if template is not None:
                    template.ensure_valid()
            except (vol.Invalid, TemplateError) as err:
                _LOGGER.error("Invalid %s for sensor %s: %s", key, record["name"], err)
                template = None
                self._template_error = True
                self._attr_available = False
            if template is not None:
                template.hass = self.hass
            setattr(self, "_" + key, template)
        self._attr_entity_registry_enabled_default = record.get("enabled", True)
        if self._coordinator:
            entry_id = self._coordinator.config_entry.entry_id
            self._attr_unique_id = f"{entry_id}_sensor_{record['id']}"
            if self._coordinator.config_entry.options.get("device_controls"):
                from homeassistant.helpers.device_registry import DeviceInfo

                self._attr_device_info = DeviceInfo(
                    identifiers={(DOMAIN, self._attr_unique_id)},
                    name=record["name"],
                    via_device=(DOMAIN, entry_id),
                    manufacturer=self._coordinator.shell.title,
                )
        else:
            self._attr_unique_id = record.get("unique_id", record["name"])

    def _filter_options(self):
        return {
            "exclude_types": self._record.get("exclude_types") or None,
            "unique_types": self._record.get("unique_types", False),
        }

    @property
    def _display_language(self):
        from .sensor_format import language_for

        return language_for(
            self._record.get("language", "en"),
            self.hass.config.language if self.hass else "en",
        )

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

        if self._record:
            self.apply_config(self._record)
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

    def _set_state(self, upcoming: list[CollectionGroup]):
        """Set entity state with default format."""
        if len(upcoming) == 0:
            self._value = None
            self._attr_icon = Icons.GENERAL_WASTE
            self._attr_entity_picture = None
            return

        collection = upcoming[0]
        # collection::=CollectionGroup{date=2020-04-01, types=['Type1', 'Type2']}

        if self._value_template is not None:
            self._value = self._value_template.async_render_with_possible_json_value(
                collection, None
            )
        else:
            from .sensor_format import render_state

            self._value = render_state(
                collection,
                self._record.get("state_format", "types_in_days"),
                self._record.get("date_format", "iso"),
                self._display_language,
                self._separator,
            )

        self._attr_icon = collection.icon or Icons.GENERAL_WASTE
        self._attr_entity_picture = collection.picture

    def _render_date(self, collection: CollectionBase):
        if self._date_template is not None:
            return self._date_template.async_render_with_possible_json_value(
                collection, None
            )
        from .sensor_format import render_date

        return render_date(
            collection.date,
            self._record.get("date_format", "iso"),
            self._display_language,
        )

    @callback
    def _update_sensor(self):
        """Update the state and the device-state-attributes of the entity.

        Called if a new data has been fetched from the source.
        """
        if self._aggregator is None:
            return

        if getattr(self, "_template_error", False):
            self._value = None
            self._attr_extra_state_attributes = {}
            if self.hass is not None and self.enabled:
                self.async_write_ha_state()
            return

        upcoming1 = self._aggregator.get_upcoming_group_by_day(
            count=1,
            include_types=self._collection_types,
            include_today=self._include_today,
            start_index=self._event_index,
            **self._filter_options(),
        )

        self._set_state(upcoming1)

        attributes = {}

        collection_types = (
            self._detail_types()
            if self._details_format
            in (DetailsFormat.appointment_types, DetailsFormat.generic)
            else []
        )

        if self._details_format == DetailsFormat.upcoming:
            # show upcoming events list in details
            upcoming = self._aggregator.get_upcoming_group_by_day(
                count=self._count,
                leadtime=self._leadtime,
                include_types=self._collection_types,
                include_today=self._include_today,
                start_index=self._event_index,
                **self._filter_options(),
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
                    **self._filter_options(),
                )
                date = (
                    "" if len(collections) == 0 else self._render_date(collections[0])
                )
                attributes[self._type_label(t)] = date
        elif self._details_format == DetailsFormat.generic:
            # insert generic attributes into details
            attributes["types"] = [self._type_label(t) for t in collection_types]
            records = self._aggregator.get_upcoming(
                preserve_bins=True,
                leadtime=self._leadtime,
                include_types=self._collection_types,
                include_today=self._include_today,
                **self._filter_options(),
            )
            selected_dates = set(sorted({e.date for e in records})[self._event_index :])
            records = [e for e in records if e.date in selected_dates]
            if self._count is not None:
                records = records[: self._count]
            attributes["upcoming"] = [self._collection_for_sensor(c) for c in records]
            refreshtime = ""
            if self._aggregator.refreshtime is not None:
                refreshtime = self._aggregator.refreshtime.isoformat(timespec="seconds")
            attributes["last_update"] = refreshtime

        if len(upcoming1) > 0:
            # Language-neutral raw values of the next collection, so cards and
            # templates can render them in the user's own language. `daysTo`
            # used to need add_days_to; that option is still accepted.
            attributes["color"] = self._record.get("color") or upcoming1[0].color
            attributes["collections"] = upcoming1[0].as_dict()["collections"]
            attributes["daysTo"] = upcoming1[0].daysTo
            attributes["date"] = upcoming1[0].date.isoformat()
            attributes["next_types"] = list(upcoming1[0].types)

        if self._details_format == DetailsFormat.upcoming:
            attributes["upcoming"] = [
                {
                    **record,
                    **(
                        {"color": self._record["color"], "color_source": "sensor"}
                        if self._record.get("color")
                        else {}
                    ),
                }
                for group in upcoming
                for record in group.as_dict()["collections"]
            ]
        if "collections" in attributes and self._record.get("color"):
            attributes["collections"] = [
                {**c, "color": self._record["color"], "color_source": "sensor"}
                for c in attributes["collections"]
            ]
        self._attr_extra_state_attributes = attributes
        self._add_refreshtime()

        if self.hass is not None:
            self.async_write_ha_state()

    def _collection_for_sensor(self, collection):
        if self._record.get("color"):
            collection = copy(collection)
            collection.set_color(self._record["color"], source="sensor")
        return collection

    def _detail_types(self):
        candidates = (
            sorted(self._aggregator.types)
            if self._collection_types is None
            else self._collection_types
        )
        excluded = self._record.get("exclude_types")
        if not excluded:
            return candidates
        eligible = self._aggregator._filter_entries(
            self._collection_types, excluded, False
        )
        if self._collection_types is None:
            return sorted({e.type for e in eligible})
        return [
            t
            for t in candidates
            if t not in excluded
            and (
                not any(
                    self._aggregator.matches_type(e, t)
                    for e in self._aggregator._entries
                )
                or any(self._aggregator.matches_type(e, t) for e in eligible)
            )
        ]

    def _type_label(self, type_id):
        """Keep legacy attribute names in display vocabulary, with ID filters."""
        for event in self._aggregator._entries:
            if type_id in (event.type, event.waste_type.id):
                return event.type
        for shell in self._aggregator._shells:
            label = shell.get_collection_type_name(type_id)
            if label != type_id:
                return label
        return type_id


class DaysToSensor(ScheduleSensor):
    """Days until the next collection as a number, for automations."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.DAYS

    def _set_state(self, upcoming: list[CollectionGroup]):
        super()._set_state(upcoming)
        self._value = upcoming[0].daysTo if upcoming else None


class LastUpdateSensor(ScheduleSensor):
    """When the schedule was last fetched, a diagnostic timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _update_sensor(self):
        refreshtime = self._aggregator.refreshtime if self._aggregator else None
        # The fetch time is a naive local datetime; a timestamp needs a zone.
        self._value = refreshtime.astimezone() if refreshtime else None
        if self.hass is not None:
            self.async_write_ha_state()


SENSOR_CLASSES: dict[str | None, type[ScheduleSensor]] = {
    "days_to": DaysToSensor,
    "last_update": LastUpdateSensor,
}
