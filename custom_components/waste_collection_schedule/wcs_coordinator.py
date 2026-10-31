import datetime
import hashlib
import logging
from random import randrange
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_time_change,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import const
from .waste_collection_schedule import Collection, CollectionAggregator, SourceShell
from .waste_collection_schedule.service.DeviceKeyStore import get_device_key_store

_LOGGER = logging.getLogger(__name__)

CACHE_STORAGE_VERSION = 1


def cache_store(hass: HomeAssistant, entry_id: str) -> Store:
    """Return the store holding the last successfully fetched entries."""
    return Store(hass, CACHE_STORAGE_VERSION, f"{const.DOMAIN}.cache.{entry_id}")


class WCSCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from waste collection service provider."""

    _shell: SourceShell
    _aggregator: CollectionAggregator
    _day_switch_time: datetime.time
    _fetch_time: datetime.time
    _last_fetch_date: datetime.date | None

    # Entity identity is derived from the config entry id, so the entry must be
    # known for certain rather than inferred from HA's `current_entry`
    # contextvar (which types it `ConfigEntry | None`).
    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        source_shell: SourceShell,
        separator: str,
        fetch_time: str | datetime.time,
        fetch_interval_days: int,
        random_fetch_time_offset: int,
        day_switch_time: str | datetime.time,
    ):
        self._hass = hass
        self._shell = source_shell
        self._store = cache_store(hass, config_entry.entry_id)
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
        # `DataUpdateCoordinator.__init__` only grew a `config_entry` keyword in
        # HA 2024.11; this integration still supports 2024.4, so set it after
        # the base class has picked the value up from the contextvar.
        self.config_entry = config_entry

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        if not await self._fetch_now():
            if not await self._async_restore_cache():
                raise UpdateFailed(
                    f"Unable to fetch waste collection data from {self.shell.title}"
                )
            _LOGGER.warning(
                "Unable to fetch waste collection data from %s, using cached data from %s",
                self.shell.title,
                self.shell.refreshtime,
            )
        self._async_track_timers()
        return {}

    async def _async_restore_cache(self) -> bool:
        """Restore the entries of the last successful fetch, e.g. after a restart."""
        data = await self._store.async_load()
        # a reconfigured entry keeps its ID; never show the old address's dates
        if not data or data.get("source_hash") != self._source_hash:
            return False
        # cached entries already have customize and day offset applied
        self._shell._refreshtime = datetime.datetime.fromisoformat(data["refreshtime"])
        self._shell._entries = [
            Collection(
                date=datetime.date.fromisoformat(e["date"]),
                t=e["type"],
                icon=e.get("icon"),
                picture=e.get("picture"),
                location=e.get("location"),
                description=e.get("description"),
            )
            for e in data["entries"]
        ]
        return True

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
    def _source_hash(self) -> str:
        # hashed, as source args can contain credentials
        return hashlib.sha256(self.shell.unique_id.encode()).hexdigest()

    @property
    def separator(self):
        return self._separator

    @property
    def day_switch_time(self):
        return self._day_switch_time

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(const.DOMAIN, self.config_entry.entry_id)},
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
            randrange(0, 60 * self._random_fetch_time_offset)
            if self._random_fetch_time_offset > 0
            else 0,
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
                await self._store.async_save(
                    {
                        "source_hash": self._source_hash,
                        "refreshtime": self.shell.refreshtime.isoformat(),
                        "entries": self.shell._entries,
                    }
                )

                # Save device keys to storage after fetch
                device_store = get_device_key_store()
                if device_store:
                    await device_store.async_save()

        await self._update_sensors_callback()
        return fetch_succeeded if self.shell else True
