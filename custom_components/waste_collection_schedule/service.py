from homeassistant.core import HomeAssistant, ServiceCall

from . import const
from .waste_collection_api import WasteCollectionApi
from .wcs_coordinator import WCSCoordinator


def get_fetch_all_service(hass: HomeAssistant):
    async def async_fetch_data(service: ServiceCall) -> None:
        for entry_id, coordinator in hass.data[const.DOMAIN].items():
            if isinstance(coordinator, WCSCoordinator):
                hass.add_job(coordinator._fetch_now)
            elif isinstance(coordinator, WasteCollectionApi):
                hass.add_job(coordinator._fetch)

    return async_fetch_data
