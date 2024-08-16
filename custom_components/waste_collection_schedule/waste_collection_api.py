# This is the class organizing the different sources when using the yaml configuration
from random import randrange

import homeassistant.util.dt as dt_util
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_change

from . import const
from .waste_collection_schedule import SourceShell

from homeassistant.helpers.event import async_call_later  # isort:skip


class WasteCollectionApi:
    """Class to manage the waste collection sources when using the yaml configuration."""

    def __init__(
        self, hass, separator, fetch_time, random_fetch_time_offset, day_switch_time
    ):
        self._hass = hass
        self._source_shells = []
        self._separator = separator
        self._fetch_time = fetch_time
        self._random_fetch_time_offset = random_fetch_time_offset
        self._day_switch_time = day_switch_time

        # start timer to fetch date once per day
        async_track_time_change(
            hass,
            self._fetch_callback,
            self._fetch_time.hour,
            self._fetch_time.minute,
            self._fetch_time.second,
        )

        # start timer for day-switch time
        if self._day_switch_time != self._fetch_time:
            async_track_time_change(
                hass,
                self._update_sensors_callback,
                self._day_switch_time.hour,
                self._day_switch_time.minute,
                self._day_switch_time.second,
            )

        # add a timer at midnight (if not already there) to update days-to
        midnight = dt_util.parse_time("00:00")
        if midnight != self._fetch_time and midnight != self._day_switch_time:
            async_track_time_change(
                hass,
                self._update_sensors_callback,
                midnight.hour,
                midnight.minute,
                midnight.second,
            )

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

    def add_source_shell(
        self,
        source_name,
        customize,
        source_args,
        calendar_title,
        day_offset,
    ):
        new_shell = SourceShell.create(
            source_name=source_name,
            customize=customize,
            source_args=source_args,
            calendar_title=calendar_title,
            day_offset=day_offset,
        )

        if new_shell:
            self._source_shells.append(new_shell)
        return new_shell

    def _fetch(self, *_):
        for shell in self._source_shells:
            shell.fetch()

        self._update_sensors_callback()

    @property
    def shells(self):
        return self._source_shells

    def get_shell(self, index):
        return self._source_shells[index] if index < len(self._source_shells) else None

    @callback
    def _fetch_callback(self, *_):
        async_call_later(
            self._hass,
            randrange(0, 60 * self._random_fetch_time_offset),
            self._fetch_now_callback,
        )

    @callback
    def _fetch_now_callback(self, *_):
        self._hass.add_job(self._fetch)

    @callback
    def _update_sensors_callback(self, *_):
        dispatcher_send(self._hass, const.UPDATE_SENSORS_SIGNAL)
