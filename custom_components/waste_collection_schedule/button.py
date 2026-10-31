"""Catalogue creation and explicit custom-sensor deletion."""

from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .sensor_controls import SensorControl, setup_controls
from .sensor_manager import SENSOR_CONFIG_SIGNAL
from .sensor_model import catalogue_id


class DeleteSensorButton(SensorControl, ButtonEntity):
    async def async_press(self):
        await self.manager.async_delete(self.sensor_id)


class CreateSensorButton(ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_should_poll = False

    def __init__(self, manager, origin, record):
        self.manager = manager
        self.origin = origin
        self._attr_name = "Create " + record["name"] + " sensor"
        self._attr_unique_id = (
            manager.entry.entry_id + "_create_" + catalogue_id(origin)
        )
        self._attr_device_info = manager.coordinator.device_info

    async def async_press(self):
        await self.manager.async_add_from_catalogue(self.origin)


async def async_setup_entry(hass, entry, async_add_entities):
    await setup_controls(
        hass,
        entry,
        async_add_entities,
        lambda manager, record: (
            [DeleteSensorButton(manager, record["id"], "delete", "Delete sensor")]
            if record["origin"] == "custom"
            else []
        ),
    )
    if not entry.options.get("device_controls"):
        return
    manager = hass.data[DOMAIN][entry.entry_id].sensor_manager
    known = set()

    @callback
    def discover():
        offered = manager.catalogue
        missing = set(offered) - known
        known.update(missing)
        async_add_entities(
            [CreateSensorButton(manager, key, offered[key]) for key in sorted(missing)]
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SENSOR_CONFIG_SIGNAL + entry.entry_id, discover)
    )
    discover()
