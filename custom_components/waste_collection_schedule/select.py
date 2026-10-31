"""Built-in sensor display choices on optional native device pages."""

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .sensor_controls import CONTROL_KEYS, SensorControl, setup_controls
from .sensor_model import DATE_FORMATS, DETAILS_FORMATS, LANGUAGES, STATE_FORMATS

CHOICES = {
    "state_format": STATE_FORMATS,
    "language": LANGUAGES,
    "date_format": DATE_FORMATS,
    "details_format": DETAILS_FORMATS,
}


class SensorSelect(SensorControl, SelectEntity):
    def __init__(self, manager, sensor_id, key):
        values = CHOICES[key]
        super().__init__(manager, sensor_id, key)
        self._attr_options = list(values)
        self._attr_translation_key = key

    @property
    def current_option(self):
        return self.record[self.key] if self.record else None

    async def async_select_option(self, option):
        if (
            self.key == "state_format"
            and option == "custom"
            and not self.record.get("value_template")
        ):
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="custom_template_required"
            )
        patch = {self.key: option}
        if self.key == "date_format":
            patch["date_template"] = None
        if self.key == "state_format" and option != "custom":
            patch["value_template"] = None
        await self.manager.async_update(self.sensor_id, patch)


async def async_setup_entry(hass, entry, async_add_entities):
    await setup_controls(
        hass,
        entry,
        async_add_entities,
        lambda manager, record: [
            SensorSelect(manager, record["id"], key)
            for key in CHOICES
            if key in CONTROL_KEYS[record["kind"]]
        ],
    )
