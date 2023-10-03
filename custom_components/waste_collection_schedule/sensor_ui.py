import logging

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription)
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .init_ui import WCSDataUpdateCoordinator as DataUpdateCoordinator
from .init_ui import WCSEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up platform for a new integration.

    Called by the HA framework after async_setup_platforms has been called
    during initialization of a new integration.
    """
    print("async_setup_entry sensor")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = [WCSSensorEntity(coordinator)]

    async_add_entities(entities)


class WCSSensorEntity(WCSEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="all_waste_types",
        name="All Waste Types",
        icon="mdi:trash-can",
        native_unit_of_measurement="",
        device_class=SensorDeviceClass.ENUM,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)

    @property
    def native_value(self) -> StateType:
        upcoming = self._aggregator.get_upcoming_group_by_day()

        if len(upcoming) == 0:
            return None

        collection = upcoming[0]
        return f"{', '.join(collection.types)} in {collection.daysTo} days"

    @property
    def extra_state_attributes(self):
        data = []

        return {
            #            ATTR_DATA: data,
            #            ATTR_PRICE_CT_PER_KWH: to_ct_per_kwh(self.native_value),
        }
