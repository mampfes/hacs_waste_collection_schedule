import asyncio
import datetime
import hashlib
import json
import logging
from dataclasses import dataclass, field
from random import randrange
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_time_change,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import const
from .waste_collection_schedule import CollectionAggregator, SourceShell
from .waste_collection_schedule.service.DeviceKeyStore import get_device_key_store

_LOGGER = logging.getLogger(__name__)
FETCH_WARNING_SECONDS = 120

CACHE_STORAGE_VERSION = 1
FETCH_STATES = f"{const.DOMAIN}_fetch_states"
# minutes between fetch retries while running on cached data; the last repeats
CACHE_RETRY_MINUTES = (5, 15, 60)
# options that shape the fetched entries besides customize, see SourceShell.create
CACHE_KEY_OPTIONS = (
    const.CONF_DAY_OFFSET,
    const.CONF_IGNORE_DUPLICATES,
    const.CONF_SHOW_ORIGINAL_LABEL,
)


@dataclass
class _EntryFetchState:
    """Fetch ownership and disk access shared across an entry's coordinators."""

    source: dict[str, Any]
    cache_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    fetch_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    last_success: "WCSCoordinator | None" = None


def cache_store(hass: HomeAssistant, entry_id: str) -> Store:
    """Return the store holding the last successfully fetched entries."""
    return Store(
        hass, CACHE_STORAGE_VERSION, f"{const.DOMAIN}.cache.{entry_id}", private=True
    )


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
        # One lock per entry and source args, kept across reloads and setup
        # retries: cancelling a fetch cannot stop its worker, so a coordinator for
        # the same source must not race it. Changed args get a new lock instead
        # of waiting for a hung fetch of the old ones.
        states = hass.data.setdefault(FETCH_STATES, {})
        source = dict(config_entry.data)
        state = states.get(config_entry.entry_id)
        if state is None or state.source != source:
            state = states[config_entry.entry_id] = _EntryFetchState(
                source, cache_lock=state.cache_lock if state else asyncio.Lock()
            )
        self._fetch_state = state
        self._fetch_lock = state.fetch_lock
        self._setup_timed_out = False
        # Fixed at creation: a fetch that outlives a reconfigure must not save
        # the old address's schedule under the new configuration's key.
        shaping = [
            source,
            {k: config_entry.options.get(k) for k in CACHE_KEY_OPTIONS},
            # pairs, not a dict: glob rules match in definition order
            list(config_entry.options.get(const.CONF_CUSTOMIZE, {}).items()),
        ]
        dump = json.dumps(shaping, sort_keys=True, default=str)
        self._cache_key = hashlib.sha256(dump.encode()).hexdigest()
        self._fetch_tracker: CALLBACK_TYPE | None = None
        self._day_switch_tracker: CALLBACK_TYPE | None = None
        self._midnight_tracker: CALLBACK_TYPE | None = None
        self._fetch_later_unsub: CALLBACK_TYPE | None = None
        self._retry_unsub: CALLBACK_TYPE | None = None
        self._retry_count = 0

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
            raise UpdateFailed(
                f"Unable to fetch waste collection data from {self.shell.title}"
            )
        self._async_track_timers()
        return {}

    async def async_restore_cache(self) -> bool:
        """Restore the entries of the last successful fetch, e.g. after a restart."""
        # same package as the sources, so restored entries equal fetched ones
        from waste_collection_schedule.collection import Collection

        try:
            # Unsupported versions and failed reads are just a cache miss.
            async with self._fetch_state.cache_lock:
                data = await self._store.async_load()
            # a reconfigured entry keeps its ID; never show the old address's dates
            if not isinstance(data, dict) or data.get("key") != self._cache_key:
                return False
            entries, sensor_entries = (
                [Collection.from_storage_dict(e) for e in data[key]]
                for key in ("entries", "sensor_entries")
            )
            raw_labels = data["raw_labels"]
            refreshtime = datetime.datetime.fromisoformat(data["refreshtime"])
        except (
            HomeAssistantError,
            KeyError,
            NotImplementedError,
            TypeError,
            ValueError,
        ):
            _LOGGER.warning("Ignoring unreadable cache of %s", self.shell.title)
            return False
        # only past dates left: fail setup as before instead of hiding it
        if not any(e.date >= datetime.date.today() for e in entries):
            return False
        self._shell._entries = entries
        # sensors read the bins before the calendar merges them
        self._shell._sensor_entries = sensor_entries
        self._shell._raw_labels = raw_labels
        self._shell._refreshtime = refreshtime
        return True

    async def async_fetch_with_retry(self, *_) -> None:
        """Fetch, retrying with backoff until it succeeds, e.g. on cached data."""
        self._retry_unsub = None
        if await self._fetch_now() or self._shutdown_requested:
            self._retry_count = 0
            return
        minutes = CACHE_RETRY_MINUTES[
            min(self._retry_count, len(CACHE_RETRY_MINUTES) - 1)
        ]
        self._retry_count += 1
        self._retry_unsub = async_call_later(
            self._hass,
            datetime.timedelta(minutes=minutes),
            self.async_fetch_with_retry,
        )

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
            "_retry_unsub",
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
    def _superseded(self) -> bool:
        # entry removed (async_remove_entry drops its state) or source args changed
        states = self._hass.data.get(FETCH_STATES, {})
        return states.get(self.config_entry.entry_id) is not self._fetch_state

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
            name=self.config_entry.title,
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
        # Waiting for the lock can be cancelled, e.g. by the setup timeout. The
        # fetch is shielded: cancelling cannot stop its executor worker, so it
        # keeps the lock until the worker finishes.
        await self._fetch_lock.acquire()
        return await asyncio.shield(
            self._hass.async_create_background_task(
                self._async_fetch_locked(), "Waste collection provider fetch"
            )
        )

    async def _async_fetch_locked(self) -> bool:
        try:
            if self._shutdown_requested:
                return False
            today = datetime.date.today()
            previous = self._fetch_state.last_success
            if (
                previous is not None
                and previous._setup_timed_out
                and previous._cache_key == self._cache_key
                and previous.shell.refreshtime.date() == today
            ):
                # A completed setup fetch is valid even if it returned no dates.
                self._shell._entries = previous.shell._entries
                self._shell._sensor_entries = previous.shell._sensor_entries
                self._shell._raw_labels = previous.shell._raw_labels
                self._shell._refreshtime = previous.shell._refreshtime
                self._last_fetch_date = previous.shell.refreshtime.date()
                self._fetch_state.last_success = None
            if (
                self._last_fetch_date is not None
                and (today - self._last_fetch_date).days < self._fetch_interval_days
            ):
                await self._update_sensors_callback()
                return True

            if self.shell:

                @callback
                def warn_slow_fetch(_now: Any) -> None:
                    _LOGGER.warning(
                        "Fetching from %s has taken more than %s seconds; later "
                        "fetches for this source will wait until it finishes",
                        self.shell.title,
                        FETCH_WARNING_SECONDS,
                    )

                cancel_warning = async_call_later(
                    self._hass, FETCH_WARNING_SECONDS, warn_slow_fetch
                )
                try:
                    fetch_succeeded = await self._hass.async_add_executor_job(
                        self.shell.fetch
                    )
                finally:
                    cancel_warning()
                # Also after a shutdown, so a fetch that outlived the setup timeout
                # fills the cache for the setup retry; not once superseded.
                if fetch_succeeded:
                    self._fetch_state.last_success = self
                    async with self._fetch_state.cache_lock:
                        if not self._superseded:
                            await self._store.async_save(
                                {
                                    "key": self._cache_key,
                                    "refreshtime": self.shell.refreshtime.isoformat(),
                                    "entries": [
                                        e.as_storage_dict() for e in self.shell._entries
                                    ],
                                    "sensor_entries": [
                                        e.as_storage_dict()
                                        for e in self.shell._sensor_entries
                                    ],
                                    "raw_labels": self.shell.raw_labels,
                                }
                            )
                if self._shutdown_requested:
                    return False
                if fetch_succeeded:
                    self._last_fetch_date = today

                    # Save device keys to storage after fetch
                    device_store = get_device_key_store()
                    if device_store:
                        await device_store.async_save()

            await self._update_sensors_callback()
            return fetch_succeeded if self.shell else True
        finally:
            self._fetch_lock.release()
