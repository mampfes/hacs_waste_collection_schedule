"""Enablement and optional advanced controls, stored with the shared record."""

from homeassistant.components.switch import SwitchEntity

from .sensor_controls import CONTROL_KEYS, SensorControl, setup_controls


class SensorSwitch(SensorControl, SwitchEntity):
    @property
    def is_on(self):
        return bool(self.record and self.record[self.key])

    async def async_turn_on(self, **kwargs):
        await self.manager.async_update(self.sensor_id, {self.key: True})

    async def async_turn_off(self, **kwargs):
        await self.manager.async_update(self.sensor_id, {self.key: False})


async def async_setup_entry(hass, entry, async_add_entities):
    await setup_controls(
        hass,
        entry,
        async_add_entities,
        lambda manager, record: [
            SensorSwitch(manager, record["id"], key)
            for key in ("enabled", "unique_types", "advanced")
            if key in CONTROL_KEYS[record["kind"]]
        ],
    )
