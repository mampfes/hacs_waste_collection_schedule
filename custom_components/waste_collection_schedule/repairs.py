"""Explicit cleanup of legacy sensors left behind by earlier renames."""

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN


class LegacySensorsRepairFlow(RepairsFlow):
    def __init__(self, entry_id):
        self.entry_id = entry_id

    async def async_step_init(self, user_input=None):
        # HA can supply issue metadata here; opening a repair is not confirmation.
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            registry = er.async_get(self.hass)
            for entity in er.async_entries_for_config_entry(registry, self.entry_id):
                if (
                    entity.platform == DOMAIN
                    and entity.domain == "sensor"
                    and entity.unique_id.startswith(self.entry_id + "_ui_sensor_")
                ):
                    registry.async_remove(entity.entity_id)
            return self.async_create_entry(data={})
        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))


async def async_create_fix_flow(hass, issue_id, data):
    if issue_id.startswith("legacy_sensors_") and data:
        return LegacySensorsRepairFlow(data["entry_id"])
    return None
