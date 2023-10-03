"""Waste Collection Schedule Component."""
import logging
import site
from pathlib import Path
from random import randrange
from typing import Any

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.event import (async_call_later,  # isort:skip
                                         async_track_time_change)
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)

from .const import (CONF_SOURCE_ARGS, CONF_SOURCE_NAME, DOMAIN,
                    UPDATE_SENSORS_SIGNAL)

# add module directory to path
package_dir = Path(__file__).resolve().parents[0]
site.addsitedir(str(package_dir))
from waste_collection_schedule import Customize, SourceShell, CollectionAggregator  # type: ignore # isort:skip # noqa: E402

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up component from a config entry,
    config_entry contains data from config entry database."""

    shell = SourceShell.create(
        source_name=entry.data[CONF_SOURCE_NAME],
        source_args=entry.data[CONF_SOURCE_ARGS],
        customize={},  # TODO
        calendar_title="",  # TODO
    )

    try:
        await hass.async_add_job(shell.fetch)
    except Exception as err:  # pylint: disable=broad-except
        ex = ConfigEntryNotReady()
        ex.__cause__ = err
        raise ex

    coordinator = WCSDataUpdateCoordinator(hass, shell=shell)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(on_update_options_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    print(f"unload {entry.entry_id}")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def on_update_options_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    # coordinator.update_interval = timedelta(seconds=entry.options[CONF_SCAN_INTERVAL])


class WCSDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from waste collection service provider."""

    _shell: SourceShell
    _aggregator: CollectionAggregator

    def __init__(
        self,
        hass: HomeAssistant,
        shell: SourceShell,  # separator, fetch_time, random_fetch_time_offset, day_switch_time
    ):
        self._hass = hass
        self._shell = shell
        self._aggregator = CollectionAggregator([shell])
        self._separator = None
        self._fetch_time = dt_util.parse_time("01:00")  # TODO
        self._random_fetch_time_offset = 60
        self._day_switch_time = dt_util.parse_time("09:00")  # TODO

        super().__init__(hass, _LOGGER, name=DOMAIN)

        # start timer to fetch date once per day
        self._fetch_tracker = async_track_time_change(
            hass,
            self._fetch_callback,
            self._fetch_time.hour,
            self._fetch_time.minute,
            self._fetch_time.second,
        )

        # start timer for day-switch time
        if self._day_switch_time != self._fetch_time:
            async_track_time_change(  # TODO: cancel on unload
                hass,
                self._update_sensors_callback,
                self._day_switch_time.hour,
                self._day_switch_time.minute,
                self._day_switch_time.second,
            )

        # add a timer at midnight (if not already there) to update days-to
        midnight = dt_util.parse_time("00:00")
        if midnight != self._fetch_time and midnight != self._day_switch_time:
            async_track_time_change(  # TODO: cancel on unload
                hass,
                self._update_sensors_callback,
                midnight.hour,
                midnight.minute,
                midnight.second,
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        # self.source.update_time()
        print("update data coordinator")
        pass

    @property
    def separator(self):
        """Separator string, used to separator waste types."""
        return self._separator

    @property
    def fetch_time(self):
        """When to fetch to data."""
        return self._fetch_time

    @property
    def day_switch_time(self):
        """When to hide entries for today."""
        return self._day_switch_time

    def _fetch(self, *_):
        for shell in self._source_shells:
            shell.fetch()

        self._update_sensors_callback()

    @property
    def shells(self):
        return self._source_shells

    def get_shell(self, index):
        return self._source_shells[index] if index < len(self._source_shells) else None

    # @callback
    async def _fetch_callback(self, *_):
        async_call_later(
            self._hass,
            randrange(0, 60 * self._random_fetch_time_offset),
            self._fetch_now_callback,
        )

    # @callback
    async def _fetch_now_callback(self, *_):
        self._hass.add_job(self._fetch)

    # @callback
    async def _update_sensors_callback(self, *_):
        dispatcher_send(self._hass, UPDATE_SENSORS_SIGNAL)


class WCSEntity(CoordinatorEntity, Entity):
    """A entity implementation for EPEX Spot service."""

    _coordinator: WCSDataUpdateCoordinator
    _shell: SourceShell
    _aggregator: CollectionAggregator
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: WCSDataUpdateCoordinator, description: EntityDescription
    ):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._shell = coordinator._shell
        self._aggregator = coordinator._aggregator
        self._attr_unique_id = f"{self._shell.unique_id} {description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._shell.unique_id}")},
            name="Waste Collection Schedule",
            manufacturer=self._shell.name,
            model=self._shell.title,
            entry_type=DeviceEntryType.SERVICE,
        )


#    @property
#    def available(self) -> bool:
#        return super().available and self._shell._marketdata_now is not None
