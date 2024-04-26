"""Config flow setup logic."""
import logging
import site
from pathlib import Path
from random import randrange
from typing import Any

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.helpers.event import async_call_later  # isort:skip
from homeassistant.helpers.event import async_track_time_change  # isort:skip
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)
from homeassistant.helpers.dispatcher import dispatcher_send
from pathlib import Path
package_dir = Path(__file__).resolve().parents[0]
site.addsitedir(str(package_dir))

from .const import *

from waste_collection_schedule import Customize, SourceShell, CollectionAggregator  # type: ignore # isort:skip # noqa: E402

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["calendar", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up component from a config entry,
    entry contains data from config entry database."""
    options = entry.options

    shell = SourceShell.create(
        source_name=entry.data[CONF_SOURCE_NAME],
        source_args=entry.data[CONF_SOURCE_ARGS],
        customize={},  # TODO
        calendar_title=options.get(CONF_SOURCE_CALENDAR_TITLE)
    )

    try:
        await hass.async_add_executor_job(shell.fetch)
    except Exception as err:  # pylint: disable=broad-except
        ex = ConfigEntryNotReady()
        ex.__cause__ = err
        raise ex

    coordinator = WCSCoordinator(
        hass,
        shell=shell,
        separator=options.get(CONF_SEPARATOR, CONF_SEPARATOR_DEFAULT),
        fetch_time=cv.time(options.get(CONF_FETCH_TIME, CONF_FETCH_TIME_DEFAULT)),
        random_fetch_time_offset=options.get(CONF_RANDOM_FETCH_TIME_OFFSET, CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT),
        day_switch_time=cv.time(options.get(CONF_DAY_SWITCH_TIME, CONF_DAY_SWITCH_TIME_DEFAULT)),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_update_listener(hass, entry):
    # Reload this instance
    await hass.config_entries.async_reload(entry.entry_id)

    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass, config_entry) -> bool:
    """Migrate old entry."""
    # Version number has gone backwards
    if CONFIG_VERSION < config_entry.version:
        _LOGGER.error(
            "Backwards migration not possible. Please update the integration.")
        return False

    # Version number has gone up
    if config_entry.version < CONFIG_VERSION:
        _LOGGER.debug("Migrating from version %s", config_entry.version)
        new_data = config_entry.data

        config_entry.version = CONFIG_VERSION
        hass.config_entries.async_update_entry(config_entry, data=new_data)

        _LOGGER.debug("Migration to version %s successful",
                      config_entry.version)

    return True


class WCSCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from waste collection service provider."""

    _shell: SourceShell
    _aggregator: CollectionAggregator

    def __init__(
        self,
        hass: HomeAssistant,
        shell: SourceShell,
        separator,
        fetch_time,
        random_fetch_time_offset,
        day_switch_time
    ):
        self._hass = hass
        self._shell = shell
        self._aggregator = CollectionAggregator([shell])
        self._separator = separator
        self._fetch_time = dt_util.parse_time(fetch_time)
        self._random_fetch_time_offset = random_fetch_time_offset
        self._day_switch_time = dt_util.parse_time(day_switch_time)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN
        )

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
        await self._fetch_now()

    @property
    def shell(self):
        return self._shell

    @property
    def separator(self):
        return self._separator

    @property
    def day_switch_time(self):
        return self._day_switch_time

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.shell.unique_id}")},
            name="Waste Collection Schedule",
            manufacturer=self.shell.title,
            model="Waste Collection Schedule",
            entry_type=DeviceEntryType.SERVICE
        )

    @callback
    async def _fetch_callback(self, *_):
        async_call_later(
            self._hass,
            randrange(0, 60 * self._random_fetch_time_offset),
            self._fetch_now,
        )

    @callback
    async def _update_sensors_callback(self, *_):
        dispatcher_send(self._hass, UPDATE_SENSORS_SIGNAL)

    async def _fetch_now(self, *_):
        if self.shell:
            await self._hass.async_add_executor_job(self.shell.fetch)

        await self._update_sensors_callback()
