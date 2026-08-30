import datetime
import logging
from random import randrange
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_time_change,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import const
from .waste_collection_schedule import CollectionAggregator, SourceShell
from .waste_collection_schedule.service.DeviceKeyStore import get_device_key_store

_LOGGER = logging.getLogger(__name__)


class WCSCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from waste collection service provider."""

    _shell: SourceShell
    _aggregator: CollectionAggregator
    _day_switch_time: datetime.time
    _fetch_time: datetime.time
    _last_fetch_date: datetime.date | None

    def __init__(
        self,
        hass: HomeAssistant,
        source_shell: SourceShell,
        separator: str,
        fetch_time: str | datetime.time,
        fetch_interval_days: int,
        random_fetch_time_offset: int,
        day_switch_time: str | datetime.time,
    ):
        self._hass = hass
        self._shell = source_shell
        self._aggregator = CollectionAggregator([source_shell])
        self._separator = separator
        fetch_time_new = (
            dt_util.parse_time(fetch_time)
            if isinstance(fetch_time, str)
            else fetch_time
        )
        if not fetch_time_new:
            raise ValueError(f"Invalid fetch_time: {fetch_time}")
        self._fetch_time = fetch_time_new
        self._fetch_interval_days = max(1, fetch_interval_days)
        self._random_fetch_time_offset = random_fetch_time_offset
        self._last_fetch_date = None
        self._fetch_tracker: CALLBACK_TYPE | None = None
        self._day_switch_tracker: CALLBACK_TYPE | None = None
        self._midnight_tracker: CALLBACK_TYPE | None = None
        self._fetch_later_unsub: CALLBACK_TYPE | None = None

        day_switch_time_new = (
            dt_util.parse_time(day_switch_time)
            if isinstance(day_switch_time, str)
            else day_switch_time
        )
        if not day_switch_time_new:
            raise ValueError(f"Invalid day_switch_time: {day_switch_time}")
        self._day_switch_time = day_switch_time_new

        super().__init__(hass, _LOGGER, name=const.DOMAIN)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        if not await self._fetch_now():
            raise UpdateFailed(
                f"Unable to fetch waste collection data from {self.shell.title}"
            )
        self._async_track_timers()
        return {}

    async def async_shutdown(self) -> None:
        """Cancel scheduled coordinator callbacks."""
        await super().async_shutdown()
        self._async_unsub_timers()

    @callback
    def _async_unsub_timers(self) -> None:
        """Cancel custom timers managed outside DataUpdateCoordinator."""
        for attr in (
            "_fetch_tracker",
            "_day_switch_tracker",
            "_midnight_tracker",
            "_fetch_later_unsub",
        ):
            if unsub := getattr(self, attr):
                unsub()
                setattr(self, attr, None)

    @callback
    def _async_track_timers(self) -> None:
        """Start custom timers after the initial fetch succeeds."""
        if self._fetch_tracker:
            return

        self._fetch_tracker = async_track_time_change(
            self._hass,
            self._fetch_callback,
            self._fetch_time.hour,
            self._fetch_time.minute,
            self._fetch_time.second,
        )

        # start timer for day-switch time
        if self._day_switch_time != self._fetch_time:
            self._day_switch_tracker = async_track_time_change(
                self._hass,
                self._update_sensors_callback,
                self._day_switch_time.hour,
                self._day_switch_time.minute,
                self._day_switch_time.second,
            )

        # add a timer at midnight (if not already there) to update days-to
        midnight = datetime.time.min
        if midnight != self._fetch_time and midnight != self._day_switch_time:
            self._midnight_tracker = async_track_time_change(
                self._hass,
                self._update_sensors_callback,
                midnight.hour,
                midnight.minute,
                midnight.second,
            )

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
            identifiers={(const.DOMAIN, f"{self.shell.unique_id}")},
            name="Waste Collection Schedule",
            manufacturer=self.shell.title,
            model="Waste Collection Schedule",
            entry_type=DeviceEntryType.SERVICE,
        )

    @callback
    async def _fetch_callback(self, *_):
        # cancel a still pending delayed fetch before scheduling a new one so
        # that repeated triggers cannot stack up multiple fetch callbacks
        if self._fetch_later_unsub:
            self._fetch_later_unsub()
            self._fetch_later_unsub = None

        self._fetch_later_unsub = async_call_later(
            self._hass,
            randrange(0, 60 * self._random_fetch_time_offset),
            self._fetch_now,
        )

    @callback
    async def _update_sensors_callback(self, *_):
        dispatcher_send(self._hass, const.UPDATE_SENSORS_SIGNAL)

    async def _fetch_now(self, *_) -> bool:
        today = datetime.date.today()
        if (
            self._last_fetch_date is not None
            and (today - self._last_fetch_date).days < self._fetch_interval_days
        ):
            await self._update_sensors_callback()
            return True

        if self.shell:
            fetch_succeeded = await self._hass.async_add_executor_job(self.shell.fetch)
            if fetch_succeeded:
                self._last_fetch_date = today

                # Save device keys to storage after fetch
                device_store = get_device_key_store()
                if device_store:
                    await device_store.async_save()

        await self._update_sensors_callback()
        return fetch_succeeded if self.shell else True
