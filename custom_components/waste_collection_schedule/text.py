"""Advanced templates, name and color edits on optional sensor devices."""

import homeassistant.helpers.config_validation as cv
from homeassistant.components.text import TextEntity

from .sensor_controls import CONTROL_KEYS, SensorControl, setup_controls
from .waste_collection_schedule.colors import validate_color


class SensorText(SensorControl, TextEntity):
    _attr_native_max = 4096

    @property
    def native_value(self):
        return (self.record.get(self.key) or "") if self.record else None

    async def async_set_value(self, value):
        patch = {self.key: value or None}
        if self.key == "color" and value:
            patch["color"] = validate_color(value)
        if self.key in ("value_template", "date_template") and value:
            cv.template(value)
        if self.key == "value_template":
            patch["state_format"] = "custom" if value else "types_in_days"
        await self.manager.async_update(self.sensor_id, patch)


async def async_setup_entry(hass, entry, async_add_entities):
    await setup_controls(
        hass,
        entry,
        async_add_entities,
        lambda manager, record: [
            SensorText(manager, record["id"], key)
            for key in ("name", "value_template", "date_template", "color")
            if key in CONTROL_KEYS[record["kind"]]
        ],
    )
