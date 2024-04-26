from .const import DOMAIN, UPDATE_SENSORS_SIGNAL
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)
import logging
import site
from typing import Any
from homeassistant.core import HomeAssistant, callback
import homeassistant.util.dt as dt_util
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.dispatcher import dispatcher_send
from pathlib import Path
package_dir = Path(__file__).resolve().parents[0]
site.addsitedir(str(package_dir))
from waste_collection_schedule import Customize, SourceShell, CollectionAggregator

_LOGGER = logging.getLogger(__name__)


class WCSCoordinator(DataUpdateCoordinator[dict[str, Any]]):
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

    async def _fetch_now(self):

        if self.shell:
            await self._hass.async_add_executor_job(self.shell.fetch)

        await self._update_sensors_callback()
