"""Common identity and change notifications for native sensor controls."""

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity, EntityCategory

from .const import DOMAIN
from .sensor_manager import SENSOR_CONFIG_SIGNAL

CONTROL_KEYS = {
    "schedule": {
        "name",
        "enabled",
        "advanced",
        "unique_types",
        "state_format",
        "language",
        "date_format",
        "details_format",
        "count",
        "leadtime",
        "event_index",
        "value_template",
        "date_template",
        "color",
    },
    "days_to": {
        "name",
        "enabled",
        "advanced",
        "unique_types",
        "language",
        "date_format",
        "details_format",
        "count",
        "leadtime",
        "event_index",
        "date_template",
        "color",
    },
    "last_update": {"name", "enabled"},
}

ADVANCED_KEYS = {"event_index", "value_template", "date_template", "color"}


class SensorControl(Entity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_should_poll = False

    def __init__(self, manager, sensor_id, key, label):
        self.manager = manager
        self.sensor_id = sensor_id
        self.key = key
        self._attr_name = label
        self._attr_unique_id = f"{manager.entry.entry_id}_control_{sensor_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{manager.entry.entry_id}_sensor_{sensor_id}")},
            name=self.record["name"],
            via_device=(DOMAIN, manager.entry.entry_id),
        )
        self._attr_entity_registry_enabled_default = (
            key not in ADVANCED_KEYS or self.record.get("advanced", False)
        )

    @property
    def record(self):
        return next(
            (
                r
                for r in self.manager.entry.options.get("sensors", [])
                if r["id"] == self.sensor_id
            ),
            None,
        )

    @property
    def available(self):
        return self.record is not None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SENSOR_CONFIG_SIGNAL + self.manager.entry.entry_id,
                self._changed,
            )
        )

    @callback
    def _changed(self):
        self.async_write_ha_state()


async def setup_controls(hass, entry, async_add_entities, factory):
    manager = hass.data[DOMAIN][entry.entry_id].sensor_manager
    if not entry.options.get("device_controls"):
        return
    known = set()

    @callback
    def discover():
        desired = [
            entity
            for record in entry.options.get("sensors", [])
            for entity in factory(manager, record)
        ]
        desired_ids = {entity.unique_id for entity in desired}
        known.intersection_update(desired_ids)
        entities = [entity for entity in desired if entity.unique_id not in known]
        known.update(entity.unique_id for entity in entities)

        if entities:
            async_add_entities(entities)

    entry.async_on_unload(
        async_dispatcher_connect(hass, SENSOR_CONFIG_SIGNAL + entry.entry_id, discover)
    )
    discover()
