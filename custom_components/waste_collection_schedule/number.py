"""Native numeric sensor settings, including distinct unlimited values."""

from homeassistant.components.number import NumberEntity, NumberMode

from .sensor_controls import CONTROL_KEYS, SensorControl, setup_controls


class SensorNumber(SensorControl, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 10000
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, manager, sensor_id, key, label):
        super().__init__(manager, sensor_id, key, label)
        self._attr_native_min_value = -1 if key == "leadtime" else 0

    @property
    def native_value(self):
        if not self.record:
            return None
        value = self.record.get(self.key)
        return (-1 if self.key == "leadtime" else 0) if value is None else value

    async def async_set_native_value(self, value):
        value = int(value)
        await self.manager.async_update(
            self.sensor_id,
            {
                self.key: None
                if (self.key == "count" and value == 0)
                or (self.key == "leadtime" and value == -1)
                else value
            },
        )


async def async_setup_entry(hass, entry, async_add_entities):
    await setup_controls(
        hass,
        entry,
        async_add_entities,
        lambda manager, record: [
            SensorNumber(manager, record["id"], key, label)
            for key, label in (
                ("count", "Count (0 = unlimited)"),
                ("leadtime", "Lead time (-1 = unlimited, 0 = today)"),
                ("event_index", "Pickup index"),
            )
            if key in CONTROL_KEYS[record["kind"]]
        ],
    )
